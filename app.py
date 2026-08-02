import os
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')

url = os.environ.get('DATABASE_URL', 'sqlite:///manoir_v2.db')
if url.startswith('postgres://'):
    url = url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
db = SQLAlchemy(app)

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


def seed():
    db.create_all()
    if User.query.count() == 0:
        pwd = generate_password_hash('Manoir2026!')
        db.session.add_all([
            User(username='SCOTT', password_hash=pwd, role='Direction'),
            User(username='MARCUS', password_hash=pwd, role='Direction'),
            User(username='KEAVON', password_hash=pwd, role='Direction'),
        ])
    if Stock.query.count() == 0:
        db.session.add_all([
            Stock(product='Eau', quantity=120, purchase_price=5, sale_price=20, alert_level=20),
            Stock(product='Soda', quantity=90, purchase_price=10, sale_price=40, alert_level=15),
            Stock(product='Bière', quantity=80, purchase_price=20, sale_price=80, alert_level=15),
            Stock(product='Vodka', quantity=25, purchase_price=50, sale_price=220, alert_level=5),
            Stock(product='Whisky', quantity=20, purchase_price=60, sale_price=250, alert_level=5),
            Stock(product='Champagne', quantity=18, purchase_price=150, sale_price=700, alert_level=5),
            Stock(product='Bouteille Premium', quantity=8, purchase_price=500, sale_price=2000, alert_level=3),
        ])
    db.session.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def direction_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'Direction':
            flash('Accès réservé à la Direction.', 'danger')
            return redirect(url_for('dashboard'))
        return view(*args, **kwargs)
    return wrapped

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().upper()
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        flash('Identifiant ou mot de passe incorrect.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    recettes = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter_by(type='recette').scalar()
    depenses = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter_by(type='depense').scalar()
    return render_template('dashboard.html', recettes=recettes, depenses=depenses,
        benefice=recettes-depenses,
        recent=Transaction.query.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(8).all(),
        upcoming=Event.query.order_by(Event.event_date.asc()).limit(5).all(),
        low_stock=Stock.query.filter(Stock.quantity <= Stock.alert_level).all())

@app.route('/transactions', methods=['GET','POST'])
@login_required
def transactions():
    if request.method == 'POST':
        db.session.add(Transaction(
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            type=request.form['type'], category=request.form['category'],
            description=request.form['description'], amount=float(request.form['amount']),
            responsible=request.form.get('responsible','')))
        db.session.commit()
        flash('Opération sauvegardée.', 'success')
        return redirect(url_for('transactions'))
    return render_template('transactions.html', rows=Transaction.query.order_by(Transaction.date.desc(), Transaction.id.desc()).all())

@app.post('/transactions/delete/<int:item_id>')
@login_required
def delete_transaction(item_id):
    db.session.delete(Transaction.query.get_or_404(item_id)); db.session.commit()
    return redirect(url_for('transactions'))

@app.route('/events', methods=['GET','POST'])
@login_required
def events():
    if request.method == 'POST':
        db.session.add(Event(name=request.form['name'], event_date=datetime.strptime(request.form['event_date'],'%Y-%m-%d').date(),
            entry_price=float(request.form['entry_price']), participants=int(request.form['participants']),
            expenses=float(request.form['expenses']), status=request.form['status']))
        db.session.commit(); flash('Événement sauvegardé.', 'success'); return redirect(url_for('events'))
    rows = Event.query.order_by(Event.event_date.desc()).all()
    for r in rows: r.estimated_profit = r.entry_price*r.participants-r.expenses
    return render_template('events.html', rows=rows)

@app.post('/events/delete/<int:item_id>')
@login_required
def delete_event(item_id):
    db.session.delete(Event.query.get_or_404(item_id)); db.session.commit(); return redirect(url_for('events'))

@app.route('/staff', methods=['GET','POST'])
@login_required
def staff():
    if request.method == 'POST':
        db.session.add(Staff(name=request.form['name'], role=request.form['role'], salary=float(request.form['salary']), status=request.form['status']))
        db.session.commit(); flash('Employé sauvegardé.', 'success'); return redirect(url_for('staff'))
    return render_template('staff.html', rows=Staff.query.order_by(Staff.role, Staff.name).all())

@app.post('/staff/delete/<int:item_id>')
@login_required
def delete_staff(item_id):
    db.session.delete(Staff.query.get_or_404(item_id)); db.session.commit(); return redirect(url_for('staff'))

@app.route('/stock', methods=['GET','POST'])
@login_required
def stock():
    if request.method == 'POST':
        db.session.add(Stock(product=request.form['product'], quantity=int(request.form['quantity']), purchase_price=float(request.form['purchase_price']), sale_price=float(request.form['sale_price']), alert_level=int(request.form['alert_level'])))
        db.session.commit(); flash('Produit sauvegardé.', 'success'); return redirect(url_for('stock'))
    rows=Stock.query.order_by(Stock.product).all()
    for r in rows: r.margin=r.sale_price-r.purchase_price
    return render_template('stock.html', rows=rows)

@app.post('/stock/update/<int:item_id>')
@login_required
def update_stock(item_id):
    row=Stock.query.get_or_404(item_id); row.quantity=max(0,int(request.form['quantity'])); db.session.commit(); return redirect(url_for('stock'))

@app.post('/stock/delete/<int:item_id>')
@login_required
def delete_stock(item_id):
    db.session.delete(Stock.query.get_or_404(item_id)); db.session.commit(); return redirect(url_for('stock'))

@app.route('/users', methods=['GET','POST'])
@direction_required
def users():
    if request.method == 'POST':
        username=request.form['username'].strip().upper(); password=request.form['password']
        if len(password)<8: flash('8 caractères minimum.', 'danger')
        elif User.query.filter_by(username=username).first(): flash('Identifiant déjà utilisé.', 'danger')
        else:
            db.session.add(User(username=username,password_hash=generate_password_hash(password),role=request.form['role']))
            db.session.commit(); flash('Compte créé.', 'success')
        return redirect(url_for('users'))
    return render_template('users.html', rows=User.query.order_by(User.role, User.username).all())

@app.post('/users/delete/<int:item_id>')
@direction_required
def delete_user(item_id):
    if item_id != session['user_id']:
        db.session.delete(User.query.get_or_404(item_id)); db.session.commit()
    return redirect(url_for('users'))

@app.route('/change-password', methods=['GET','POST'])
@login_required
def change_password():
    user=User.query.get_or_404(session['user_id'])
    if request.method=='POST':
        if not check_password_hash(user.password_hash, request.form['current_password']): flash('Mot de passe actuel incorrect.', 'danger')
        elif request.form['new_password'] != request.form['confirm_password']: flash('Les mots de passe ne correspondent pas.', 'danger')
        elif len(request.form['new_password'])<8: flash('8 caractères minimum.', 'danger')
        else:
            user.password_hash=generate_password_hash(request.form['new_password']); db.session.commit(); flash('Mot de passe modifié.', 'success'); return redirect(url_for('dashboard'))
    return render_template('change_password.html')

with app.app_context():
    seed()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
