import csv
import io
import os
from collections import Counter, defaultdict
from datetime import date, datetime
from functools import wraps

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')

url = os.environ.get('DATABASE_URL', 'sqlite:///manoir_v3.db')
if url.startswith('postgres://'):
    url = url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
db = SQLAlchemy(app)

ROLE_ACCESS = {
    'Direction': {'dashboard','transactions','events','stock','staff','users','statistics','planning','exports'},
    'Barman': {'dashboard','transactions','stock','statistics'},
    'Employé': {'dashboard','events','planning'},
    'Sécurité': {'dashboard','events','planning','staff'},
    'DJ': {'dashboard','events','planning'},
}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, default='Employé')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    responsible = db.Column(db.String(80))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    entry_price = db.Column(db.Float, default=0, nullable=False)
    participants = db.Column(db.Integer, default=0, nullable=False)
    expenses = db.Column(db.Float, default=0, nullable=False)
    status = db.Column(db.String(40), default='Prévu', nullable=False)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    salary = db.Column(db.Float, default=0, nullable=False)
    status = db.Column(db.String(40), default='Actif', nullable=False)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(140), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    purchase_price = db.Column(db.Float, default=0, nullable=False)
    sale_price = db.Column(db.Float, default=0, nullable=False)
    alert_level = db.Column(db.Integer, default=5, nullable=False)

class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=True)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(40), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    customer = db.Column(db.String(120), nullable=False, default='Client RP')
    responsible = db.Column(db.String(80))
    total_sale = db.Column(db.Float, nullable=False, default=0)
    total_purchase = db.Column(db.Float, nullable=False, default=0)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan', lazy=True)

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    stock_id = db.Column(db.Integer, nullable=True)
    product_name = db.Column(db.String(140), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_purchase_price = db.Column(db.Float, nullable=False, default=0)
    unit_sale_price = db.Column(db.Float, nullable=False, default=0)

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_name = db.Column(db.String(120), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    position = db.Column(db.String(80), nullable=False)
    notes = db.Column(db.String(255))



PRODUCT_CATALOG = [('Eau', '💧', 5, 20, 'eau.png'), ('Soda', '🥤', 10, 40, 'soda.png'), ('Bière', '🍺', 20, 80, 'biere.png'), ('Vodka', '🍸', 50, 220, 'vodka.png'), ('Whisky', '🥃', 60, 250, 'whisky.png'), ('Champagne', '🍾', 150, 700, 'champagne.png'), ('Vin rouge', '🍷', 45, 180, 'vin_rouge.png'), ('Tequila', '🥃', 55, 230, 'tequila.png'), ('Rhum', '🥃', 50, 210, 'rhum.png'), ('Cocktail', '🍹', 35, 160, 'cocktail.png'), ('Mojito', '🍹', 40, 180, 'mojito.png'), ('Cocktail sans alcool', '🍹', 20, 90, 'cocktail_sans_alcool.png'), ('Bouteille Premium', '💎', 500, 2000, 'premium.png'), ('Red Bull', '⚡', 15, 70, 'red_bull.png'), ('Jus de fruits', '🧃', 12, 50, 'jus.png'), ('Café', '☕', 8, 35, 'cafe.png'), ('Chips', '🍟', 12, 55, 'chips.png'), ('Burger', '🍔', 40, 140, 'burger.png'), ('Pizza', '🍕', 55, 180, 'pizza.png'), ('Hot-dog', '🌭', 30, 110, 'hot_dog.png'), ('Sushi', '🍣', 70, 240, 'sushi.png'), ('Cigare', '🚬', 80, 300, 'cigare.png')]
PRODUCT_ICON_MAP = {name.lower(): filename for name, emoji, buy, sell, filename in PRODUCT_CATALOG}
PRODUCT_EMOJI_MAP = {name.lower(): emoji for name, emoji, buy, sell, filename in PRODUCT_CATALOG}

def product_icon(product_name):
    return PRODUCT_ICON_MAP.get((product_name or '').strip().lower(), 'default.png')

def product_emoji(product_name):
    return PRODUCT_EMOJI_MAP.get((product_name or '').strip().lower(), '🛍️')


def seed():
    db.create_all()
    if User.query.count() == 0:
        pwd = generate_password_hash('Manoir2026!')
        db.session.add_all([
            User(username='SCOTT', password_hash=pwd, role='Direction'),
            User(username='MARCUS', password_hash=pwd, role='Direction'),
            User(username='KEAVON', password_hash=pwd, role='Direction'),
        ])
    catalog_marker = AppSetting.query.filter_by(key='product_catalog_v52').first()
    if catalog_marker is None:
        for product_name, emoji, purchase_price, sale_price, icon_file in PRODUCT_CATALOG:
            row = Stock.query.filter(db.func.lower(Stock.product) == product_name.lower()).first()
            if row is None:
                row = Stock(product=product_name, quantity=100, purchase_price=purchase_price,
                            sale_price=sale_price, alert_level=10)
                db.session.add(row)
            else:
                row.quantity = 100
                row.purchase_price = purchase_price
                row.sale_price = sale_price
                row.alert_level = 10
        db.session.add(AppSetting(key='product_catalog_v52', value='installed'))
    db.session.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def access_required(section):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            allowed = ROLE_ACCESS.get(session.get('role'), {'dashboard'})
            if section not in allowed:
                flash("Tu n'as pas accès à cette partie.", 'danger')
                return redirect(url_for('dashboard'))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def direction_required(view):
    return access_required('users')(view)

@app.context_processor
def inject_access():
    return {
        'access': ROLE_ACCESS.get(session.get('role'), {'dashboard'}),
        'product_icon': product_icon,
        'product_emoji': product_emoji,
    }

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().upper()
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session.clear(); session['user_id']=user.id; session['username']=user.username; session['role']=user.role
            return redirect(url_for('dashboard'))
        flash('Identifiant ou mot de passe incorrect.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    recettes = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter_by(type='recette').scalar()
    depenses = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter_by(type='depense').scalar()
    sold_items = db.session.query(db.func.coalesce(db.func.sum(InvoiceItem.quantity),0)).scalar()
    return render_template('dashboard.html', recettes=recettes, depenses=depenses, benefice=recettes-depenses,
        sold_items=sold_items, recent=Transaction.query.order_by(Transaction.date.desc(),Transaction.id.desc()).limit(8).all(),
        upcoming=Event.query.order_by(Event.event_date.asc()).limit(5).all(), low_stock=Stock.query.filter(Stock.quantity<=Stock.alert_level).all())

@app.route('/transactions', methods=['GET','POST'])
@access_required('transactions')
def transactions():
    if request.method == 'POST':
        db.session.add(Transaction(date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(), type=request.form['type'],
            category=request.form['category'], description=request.form['description'], amount=float(request.form['amount']),
            responsible=request.form.get('responsible','')))
        db.session.commit(); flash('Opération sauvegardée.', 'success'); return redirect(url_for('transactions'))
    products=Stock.query.order_by(Stock.product).all(); invoices=Invoice.query.order_by(Invoice.created_at.desc()).limit(100).all()
    return render_template('transactions.html', rows=Transaction.query.order_by(Transaction.date.desc(),Transaction.id.desc()).all(),
        products=products, invoices=invoices, today=date.today().isoformat())

@app.post('/transactions/delete/<int:item_id>')
@access_required('transactions')
def delete_transaction(item_id):
    tx=Transaction.query.get_or_404(item_id)
    linked=Invoice.query.filter_by(transaction_id=tx.id).first()
    if linked:
        flash('Cette opération appartient à une facture. Supprime la facture pour remettre le stock.', 'danger')
    else:
        db.session.delete(tx); db.session.commit(); flash('Opération supprimée.', 'success')
    return redirect(url_for('transactions'))

@app.post('/invoices/create')
@access_required('transactions')
def create_invoice():
    product_ids=request.form.getlist('product_id[]'); quantities=request.form.getlist('quantity[]')
    customer=request.form.get('customer','').strip() or 'Client RP'; responsible=request.form.get('responsible','').strip() or session.get('username','')
    invoice_date=datetime.strptime(request.form.get('invoice_date'),'%Y-%m-%d').date()
    if not product_ids or len(product_ids)!=len(quantities):
        flash('Ajoute au moins un produit.', 'danger'); return redirect(url_for('transactions'))
    aggregate=defaultdict(int)
    try:
        for pid,qty_raw in zip(product_ids,quantities):
            if not pid: continue
            qty=int(qty_raw)
            if qty<=0: raise ValueError('Quantité invalide.')
            aggregate[int(pid)] += qty
        if not aggregate: raise ValueError('Ajoute au moins un produit.')
        prepared=[]; total_sale=0.0; total_purchase=0.0
        for pid,qty in aggregate.items():
            product=Stock.query.get(pid)
            if product is None: raise ValueError('Produit introuvable.')
            if product.quantity<qty: raise ValueError(f'Stock insuffisant pour {product.product} : {product.quantity} disponible(s).')
            prepared.append((product,qty)); total_sale+=product.sale_price*qty; total_purchase+=product.purchase_price*qty
        number=f'PB-{datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:22]}'
        description='Facture '+number+' — '+', '.join(f'{q}× {p.product}' for p,q in prepared)
        tx=Transaction(date=invoice_date,type='recette',category='Vente produits',description=description,amount=total_sale,responsible=responsible)
        db.session.add(tx); db.session.flush()
        invoice=Invoice(invoice_number=number,date=invoice_date,customer=customer,responsible=responsible,total_sale=total_sale,total_purchase=total_purchase,transaction_id=tx.id)
        db.session.add(invoice); db.session.flush()
        for product,qty in prepared:
            product.quantity-=qty
            db.session.add(InvoiceItem(invoice_id=invoice.id,stock_id=product.id,product_name=product.product,quantity=qty,
                unit_purchase_price=product.purchase_price,unit_sale_price=product.sale_price))
        db.session.commit(); flash(f'Facture {number} créée. Stock et comptabilité mis à jour.', 'success')
        return redirect(url_for('invoice_detail',invoice_id=invoice.id))
    except Exception as exc:
        db.session.rollback(); flash(str(exc),'danger'); return redirect(url_for('transactions'))

@app.get('/invoices/<int:invoice_id>')
@access_required('transactions')
def invoice_detail(invoice_id):
    return render_template('invoice_detail.html', invoice=Invoice.query.get_or_404(invoice_id))

@app.post('/invoices/delete/<int:invoice_id>')
@direction_required
def delete_invoice(invoice_id):
    invoice=Invoice.query.get_or_404(invoice_id)
    for item in invoice.items:
        if item.stock_id:
            product=Stock.query.get(item.stock_id)
            if product: product.quantity+=item.quantity
    if invoice.transaction_id:
        tx=Transaction.query.get(invoice.transaction_id)
        if tx: db.session.delete(tx)
    db.session.delete(invoice); db.session.commit(); flash('Facture supprimée et stock restauré.','success')
    return redirect(url_for('transactions'))

@app.route('/events',methods=['GET','POST'])
@access_required('events')
def events():
    if request.method=='POST':
        db.session.add(Event(name=request.form['name'],event_date=datetime.strptime(request.form['event_date'],'%Y-%m-%d').date(),
            entry_price=float(request.form['entry_price']),participants=int(request.form['participants']),expenses=float(request.form['expenses']),status=request.form['status']))
        db.session.commit(); flash('Événement sauvegardé.','success'); return redirect(url_for('events'))
    rows=Event.query.order_by(Event.event_date.desc()).all()
    for r in rows:r.estimated_profit=r.entry_price*r.participants-r.expenses
    return render_template('events.html',rows=rows)

@app.post('/events/delete/<int:item_id>')
@access_required('events')
def delete_event(item_id):
    db.session.delete(Event.query.get_or_404(item_id));db.session.commit();return redirect(url_for('events'))

@app.route('/staff',methods=['GET','POST'])
@access_required('staff')
def staff():
    if request.method=='POST':
        db.session.add(Staff(name=request.form['name'],role=request.form['role'],salary=float(request.form['salary']),status=request.form['status']))
        db.session.commit();flash('Employé sauvegardé.','success');return redirect(url_for('staff'))
    return render_template('staff.html',rows=Staff.query.order_by(Staff.role,Staff.name).all())

@app.post('/staff/delete/<int:item_id>')
@access_required('staff')
def delete_staff(item_id):
    db.session.delete(Staff.query.get_or_404(item_id));db.session.commit();return redirect(url_for('staff'))

@app.route('/stock',methods=['GET','POST'])
@access_required('stock')
def stock():
    if request.method=='POST':
        db.session.add(Stock(product=request.form['product'],quantity=int(request.form['quantity']),purchase_price=float(request.form['purchase_price']),sale_price=float(request.form['sale_price']),alert_level=int(request.form['alert_level'])))
        db.session.commit();flash('Produit sauvegardé.','success');return redirect(url_for('stock'))
    rows=Stock.query.order_by(Stock.product).all()
    for r in rows:r.margin=r.sale_price-r.purchase_price
    return render_template('stock.html',rows=rows)

@app.post('/stock/update/<int:item_id>')
@access_required('stock')
def update_stock(item_id):
    row=Stock.query.get_or_404(item_id);row.quantity=max(0,int(request.form['quantity']));db.session.commit();flash('Stock mis à jour.','success');return redirect(url_for('stock'))

@app.post('/stock/delete/<int:item_id>')
@access_required('stock')
def delete_stock(item_id):
    db.session.delete(Stock.query.get_or_404(item_id));db.session.commit();return redirect(url_for('stock'))

@app.route('/planning',methods=['GET','POST'])
@access_required('planning')
def planning():
    if request.method=='POST':
        db.session.add(Shift(staff_name=request.form['staff_name'],shift_date=datetime.strptime(request.form['shift_date'],'%Y-%m-%d').date(),
            start_time=request.form['start_time'],end_time=request.form['end_time'],position=request.form['position'],notes=request.form.get('notes','')))
        db.session.commit();flash('Créneau ajouté au planning.','success');return redirect(url_for('planning'))
    return render_template('planning.html',rows=Shift.query.order_by(Shift.shift_date.asc(),Shift.start_time.asc()).all(),staff=Staff.query.order_by(Staff.name).all(),today=date.today().isoformat())

@app.post('/planning/delete/<int:item_id>')
@access_required('planning')
def delete_shift(item_id):
    db.session.delete(Shift.query.get_or_404(item_id));db.session.commit();return redirect(url_for('planning'))

@app.route('/statistics')
@access_required('statistics')
def statistics():
    invoices=Invoice.query.order_by(Invoice.date.asc()).all(); items=InvoiceItem.query.all(); transactions=Transaction.query.all()
    month_sales=defaultdict(float);month_expenses=defaultdict(float)
    for t in transactions:
        key=t.date.strftime('%Y-%m')
        if t.type=='recette':month_sales[key]+=t.amount
        else:month_expenses[key]+=t.amount
    months=sorted(set(month_sales)|set(month_expenses))[-12:]
    product_qty=Counter();product_revenue=Counter()
    for item in items:
        product_qty[item.product_name]+=item.quantity;product_revenue[item.product_name]+=item.quantity*item.unit_sale_price
    top_products=product_qty.most_common(10)
    top_sellers=Counter((i.responsible or 'Non renseigné') for i in invoices)
    return render_template('statistics.html',months=months,sales=[month_sales[m] for m in months],expenses=[month_expenses[m] for m in months],
        top_products=top_products,product_labels=[x[0] for x in top_products],product_values=[x[1] for x in top_products],
        invoice_count=len(invoices),average_invoice=(sum(i.total_sale for i in invoices)/len(invoices) if invoices else 0),
        total_margin=sum(i.total_sale-i.total_purchase for i in invoices),top_sellers=top_sellers.most_common(5))


def csv_response(filename,headers,rows):
    output=io.StringIO();writer=csv.writer(output,delimiter=';');writer.writerow(headers);writer.writerows(rows)
    data='\ufeff'+output.getvalue()
    return Response(data,mimetype='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename={filename}'})

@app.get('/export/transactions.csv')
@access_required('exports')
def export_transactions():
    rows=Transaction.query.order_by(Transaction.date.desc()).all()
    return csv_response('comptabilite_playboy.csv',['Date','Type','Catégorie','Description','Montant','Responsable'],[[r.date,r.type,r.category,r.description,r.amount,r.responsible] for r in rows])

@app.get('/export/invoices.csv')
@access_required('exports')
def export_invoices():
    rows=Invoice.query.order_by(Invoice.date.desc()).all()
    return csv_response('factures_playboy.csv',['Numéro','Date','Client','Responsable','Total vente','Coût achat','Bénéfice'],[[r.invoice_number,r.date,r.customer,r.responsible,r.total_sale,r.total_purchase,r.total_sale-r.total_purchase] for r in rows])

@app.get('/export/stock.csv')
@access_required('exports')
def export_stock():
    rows=Stock.query.order_by(Stock.product).all()
    return csv_response('stock_playboy.csv',['Produit','Quantité','Prix achat','Prix vente','Marge unité','Valeur stock achat'],[[r.product,r.quantity,r.purchase_price,r.sale_price,r.sale_price-r.purchase_price,r.quantity*r.purchase_price] for r in rows])

@app.route('/users',methods=['GET','POST'])
@direction_required
def users():
    if request.method=='POST':
        username=request.form['username'].strip().upper();password=request.form['password']
        if len(password)<8:flash('8 caractères minimum.','danger')
        elif User.query.filter_by(username=username).first():flash('Identifiant déjà utilisé.','danger')
        else:
            db.session.add(User(username=username,password_hash=generate_password_hash(password),role=request.form['role']));db.session.commit();flash('Compte créé.','success')
        return redirect(url_for('users'))
    return render_template('users.html',rows=User.query.order_by(User.role,User.username).all())

@app.post('/users/delete/<int:item_id>')
@direction_required
def delete_user(item_id):
    if item_id!=session['user_id']:db.session.delete(User.query.get_or_404(item_id));db.session.commit()
    return redirect(url_for('users'))

@app.route('/change-password',methods=['GET','POST'])
@login_required
def change_password():
    user=User.query.get_or_404(session['user_id'])
    if request.method=='POST':
        if not check_password_hash(user.password_hash,request.form['current_password']):flash('Mot de passe actuel incorrect.','danger')
        elif request.form['new_password']!=request.form['confirm_password']:flash('Les mots de passe ne correspondent pas.','danger')
        elif len(request.form['new_password'])<8:flash('8 caractères minimum.','danger')
        else:user.password_hash=generate_password_hash(request.form['new_password']);db.session.commit();flash('Mot de passe modifié.','success');return redirect(url_for('dashboard'))
    return render_template('change_password.html')

with app.app_context():seed()
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
