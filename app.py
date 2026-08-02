import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "manoir.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-public-hosting")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Direction'
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('recette','depense')),
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        responsible TEXT
    );

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        event_date TEXT NOT NULL,
        entry_price REAL NOT NULL DEFAULT 0,
        participants INTEGER NOT NULL DEFAULT 0,
        expenses REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Prévu'
    );

    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        salary REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Actif'
    );

    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        purchase_price REAL NOT NULL DEFAULT 0,
        sale_price REAL NOT NULL DEFAULT 0,
        alert_level INTEGER NOT NULL DEFAULT 5
    );
    """)

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        shared_password = generate_password_hash("Manoir2026!")
        direction_users = [
            ("SCOTT", shared_password, "Direction"),
            ("MARCUS", shared_password, "Direction"),
            ("KEAVON", shared_password, "Direction"),
        ]
        cur.executemany(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            direction_users
        )

    cur.execute("SELECT COUNT(*) FROM transactions")
    if cur.fetchone()[0] == 0:
        sample_tx = [
            ("2026-08-02","recette","Entrées","White Party - 50 entrées",7500,"Direction"),
            ("2026-08-02","recette","Bar","Ventes de champagne et cocktails",4200,"Barman"),
            ("2026-08-02","depense","DJ","Cachet du DJ",1500,"Direction"),
            ("2026-08-02","depense","Sécurité","Équipe de sécurité",1200,"Direction"),
        ]
        cur.executemany("INSERT INTO transactions(date,type,category,description,amount,responsible) VALUES(?,?,?,?,?,?)", sample_tx)

    cur.execute("SELECT COUNT(*) FROM events")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO events(name,event_date,entry_price,participants,expenses,status) VALUES(?,?,?,?,?,?)",
            [
                ("Squid Game — Playboy Manor Edition","2026-08-15",150,50,4500,"Prévu"),
                ("White Party","2026-08-22",300,0,2500,"Prévu"),
                ("Casino Royale","2026-08-29",500,0,4000,"Prévu"),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM staff")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO staff(name,role,salary,status) VALUES(?,?,?,?)",
            [
                ("Lenni","Propriétaire",0,"Actif"),
                ("Marcus","Sécurité",800,"Actif"),
                ("Heaven","Bunny",600,"Actif"),
                ("Jay","DJ",1200,"Actif"),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM stock")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO stock(product,quantity,purchase_price,sale_price,alert_level) VALUES(?,?,?,?,?)",
            [
                ("Eau",120,5,20,20),
                ("Soda",90,10,40,15),
                ("Bière",80,20,80,15),
                ("Vodka",25,50,220,5),
                ("Whisky",20,60,250,5),
                ("Champagne",18,150,700,5),
                ("Bouteille Premium",8,500,2000,3),
            ]
        )

    db.commit()
    db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def direction_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ("Direction", "Propriétaire"):
            flash("Accès réservé à la Direction.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/", methods=["GET"])
@login_required
def dashboard():
    db = get_db()
    totals = db.execute("""
        SELECT
        COALESCE(SUM(CASE WHEN type='recette' THEN amount ELSE 0 END),0) AS recettes,
        COALESCE(SUM(CASE WHEN type='depense' THEN amount ELSE 0 END),0) AS depenses
        FROM transactions
    """).fetchone()
    recent = db.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC LIMIT 8").fetchall()
    upcoming = db.execute("SELECT * FROM events ORDER BY event_date ASC LIMIT 5").fetchall()
    low_stock = db.execute("SELECT * FROM stock WHERE quantity <= alert_level ORDER BY quantity ASC").fetchall()
    return render_template("dashboard.html",
                           recettes=totals["recettes"],
                           depenses=totals["depenses"],
                           benefice=totals["recettes"]-totals["depenses"],
                           recent=recent, upcoming=upcoming, low_stock=low_stock)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Identifiant ou mot de passe incorrect.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/transactions", methods=["GET","POST"])
@login_required
def transactions():
    db = get_db()
    if request.method == "POST":
        db.execute("""
            INSERT INTO transactions(date,type,category,description,amount,responsible)
            VALUES(?,?,?,?,?,?)
        """, (
            request.form["date"],
            request.form["type"],
            request.form["category"],
            request.form["description"],
            float(request.form["amount"]),
            request.form.get("responsible","")
        ))
        db.commit()
        flash("Opération ajoutée.", "success")
        return redirect(url_for("transactions"))
    rows = db.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC").fetchall()
    return render_template("transactions.html", rows=rows)

@app.post("/transactions/delete/<int:item_id>")
@login_required
def delete_transaction(item_id):
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id=?", (item_id,))
    db.commit()
    flash("Opération supprimée.", "success")
    return redirect(url_for("transactions"))

@app.route("/events", methods=["GET","POST"])
@login_required
def events():
    db = get_db()
    if request.method == "POST":
        db.execute("""
            INSERT INTO events(name,event_date,entry_price,participants,expenses,status)
            VALUES(?,?,?,?,?,?)
        """, (
            request.form["name"], request.form["event_date"],
            float(request.form["entry_price"]), int(request.form["participants"]),
            float(request.form["expenses"]), request.form["status"]
        ))
        db.commit()
        flash("Événement ajouté.", "success")
        return redirect(url_for("events"))
    rows = db.execute("SELECT *, (entry_price*participants-expenses) AS estimated_profit FROM events ORDER BY event_date DESC").fetchall()
    return render_template("events.html", rows=rows)

@app.post("/events/delete/<int:item_id>")
@login_required
def delete_event(item_id):
    db = get_db()
    db.execute("DELETE FROM events WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("events"))

@app.route("/staff", methods=["GET","POST"])
@login_required
def staff():
    db = get_db()
    if request.method == "POST":
        db.execute("INSERT INTO staff(name,role,salary,status) VALUES(?,?,?,?)", (
            request.form["name"], request.form["role"],
            float(request.form["salary"]), request.form["status"]
        ))
        db.commit()
        flash("Employé ajouté.", "success")
        return redirect(url_for("staff"))
    rows = db.execute("SELECT * FROM staff ORDER BY role, name").fetchall()
    return render_template("staff.html", rows=rows)

@app.post("/staff/delete/<int:item_id>")
@login_required
def delete_staff(item_id):
    db = get_db()
    db.execute("DELETE FROM staff WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("staff"))

@app.route("/stock", methods=["GET","POST"])
@login_required
def stock():
    db = get_db()
    if request.method == "POST":
        db.execute("""
            INSERT INTO stock(product,quantity,purchase_price,sale_price,alert_level)
            VALUES(?,?,?,?,?)
        """, (
            request.form["product"], int(request.form["quantity"]),
            float(request.form["purchase_price"]), float(request.form["sale_price"]),
            int(request.form["alert_level"])
        ))
        db.commit()
        flash("Produit ajouté.", "success")
        return redirect(url_for("stock"))
    rows = db.execute("""
        SELECT *, (sale_price-purchase_price) AS margin
        FROM stock ORDER BY product
    """).fetchall()
    return render_template("stock.html", rows=rows)

@app.post("/stock/update/<int:item_id>")
@login_required
def update_stock(item_id):
    qty = int(request.form["quantity"])
    db = get_db()
    db.execute("UPDATE stock SET quantity=? WHERE id=?", (qty, item_id))
    db.commit()
    flash("Stock mis à jour.", "success")
    return redirect(url_for("stock"))

@app.post("/stock/delete/<int:item_id>")
@login_required
def delete_stock(item_id):
    db = get_db()
    db.execute("DELETE FROM stock WHERE id=?", (item_id,))
    db.commit()
    return redirect(url_for("stock"))

@app.route("/change-password", methods=["GET","POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form["current_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not check_password_hash(user["password_hash"], current):
            flash("Mot de passe actuel incorrect.", "danger")
        elif len(new) < 8:
            flash("Le nouveau mot de passe doit contenir au moins 8 caractères.", "danger")
        elif new != confirm:
            flash("Les deux nouveaux mots de passe ne correspondent pas.", "danger")
        else:
            db.execute("UPDATE users SET password_hash=? WHERE id=?",
                       (generate_password_hash(new), session["user_id"]))
            db.commit()
            flash("Mot de passe modifié.", "success")
            return redirect(url_for("dashboard"))
    return render_template("change_password.html")


@app.route("/users", methods=["GET","POST"])
@direction_required
def users():
    db = get_db()
    if request.method == "POST":
        username = request.form["username"].strip().upper()
        password = request.form["password"]
        role = request.form["role"]
        if len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", "danger")
        else:
            try:
                db.execute(
                    "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
                    (username, generate_password_hash(password), role)
                )
                db.commit()
                flash("Compte ajouté.", "success")
            except sqlite3.IntegrityError:
                flash("Cet identifiant existe déjà.", "danger")
        return redirect(url_for("users"))
    rows = db.execute("SELECT id,username,role FROM users ORDER BY role,username").fetchall()
    return render_template("users.html", rows=rows)

@app.post("/users/delete/<int:item_id>")
@direction_required
def delete_user(item_id):
    if item_id == session.get("user_id"):
        flash("Tu ne peux pas supprimer ton propre compte pendant ta connexion.", "danger")
        return redirect(url_for("users"))
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (item_id,))
    db.commit()
    flash("Compte supprimé.", "success")
    return redirect(url_for("users"))

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
