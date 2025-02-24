import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "finansesprogr.db")


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def execute_query(self, query, params=(), fetch_one=False, fetch_all=False, commit=False):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = None
        if fetch_one:
            data = cursor.fetchone()
        elif fetch_all:
            data = cursor.fetchall()
        if commit:
            conn.commit()
        conn.close()
        return data


class FinansuApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'supersecretkey'
        self.db = DatabaseManager(DB_PATH)
        self.setup_routes()

    def setup_routes(self):
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/register', 'register', self.register, methods=['GET', 'POST'])
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/dashboard', 'dashboard', self.dashboard)
        self.app.add_url_rule('/ienakumi', 'ienakumi', self.ienakumi)
        self.app.add_url_rule('/izdevumi', 'izdevumi', self.izdevumi)
        self.app.add_url_rule('/merki', 'merki', self.merki)
        self.app.add_url_rule('/logout', 'logout', self.logout)

    def index(self):
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    def register(self):
        if request.method == 'POST':
            lietotajvards = request.form['lietotajvards']
            parole = request.form['parole']
            parole2 = request.form['parole2']

            if parole != parole2:
                flash("Paroles nesakrīt!", "danger")
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(parole)

            user_exists = self.db.execute_query(
                "SELECT * FROM Lietotajs WHERE lietotajvards = ?", (lietotajvards,), fetch_one=True)
            if user_exists:
                flash("Lietotājvārds jau eksistē!", "danger")
                return redirect(url_for('register'))

            self.db.execute_query(
                "INSERT INTO Lietotajs (lietotajvards, parole) VALUES (?, ?)",
                (lietotajvards, hashed_password), commit=True)

            flash("Reģistrācija veiksmīga! Tagad vari pieslēgties.", "success")
            return redirect(url_for('login'))
        return render_template('register.html')

    def login(self):
        if request.method == 'POST':
            lietotajvards = request.form['lietotajvards']
            parole = request.form['parole']

            user = self.db.execute_query(
                "SELECT user_id, parole FROM Lietotajs WHERE lietotajvards = ?",
                (lietotajvards,), fetch_one=True)

            if user and check_password_hash(user[1], parole):
                session['user_id'] = user[0]
                flash("Veiksmīgi ielogojies!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Nepareizs lietotājvārds vai parole.", "danger")
        return render_template('login.html')

    def dashboard(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        ienakumi = self.db.execute_query(
            "SELECT * FROM Ienakumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        izdevumi = self.db.execute_query(
            "SELECT * FROM Izdevumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        merki = self.db.execute_query(
            "SELECT * FROM Merki WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        return render_template('dashboard.html', ienakumi=ienakumi, izdevumi=izdevumi, merki=merki)

    def ienakumi(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        ienakumi = self.db.execute_query(
            "SELECT * FROM Ienakumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)
        return render_template('ienakumi.html', ienakumi=ienakumi)

    def izdevumi(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        izdevumi = self.db.execute_query(
            "SELECT * FROM Izdevumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)
        return render_template('izdevumi.html', izdevumi=izdevumi)

    def merki(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        merki = self.db.execute_query(
            "SELECT * FROM Merki WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)
        return render_template('merki.html', merki=merki)

    def logout(self):
        session.pop('user_id', None)
        flash("Tu esi izlogojies.", "success")
        return redirect(url_for('login'))

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    app = FinansuApp()
    app.run()
