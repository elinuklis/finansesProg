import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "finansesprogr1.db")


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
        self.app.add_url_rule('/ienakumi', 'ienakumi', self.ienakumi, methods=['GET', 'POST'])
        self.app.add_url_rule('/izdevumi', 'izdevumi', self.izdevumi, methods=['GET', 'POST'])
        self.app.add_url_rule('/merki', 'merki', self.merki, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.logout)
        self.app.add_url_rule('/delete_ienakumi/<int:ienakumi_id>', 'delete_ienakumi', self.delete_ienakumi, methods=['POST'])
        self.app.add_url_rule('/delete_izdevumi/<int:izdevumi_id>', 'delete_izdevumi', self.delete_izdevumi, methods=['POST'])
        self.app.add_url_rule('/delete_merki/<int:merki_id>', 'delete_merki', self.delete_merki, methods=['POST'])

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

        kategorijas = ['Alga', 'Pārdošana', 'Pabalsts', 'Dāvana', 'Nodokļu atmaksas', 'Investīciju ienākumi', 'Cits']

        if request.method == 'POST':
            summa = request.form['summa']
            kategorija = request.form['kategorija']

            datums = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            self.db.execute_query(
                "INSERT INTO Ienakumi (user_id, summa, kategorija, datums) VALUES (?, ?, ?, ?)",
                (session['user_id'], summa, kategorija, datums), commit=True)

            flash("Ienākums veiksmīgi pievienots!", "success")
            return redirect(url_for('ienakumi'))

        ienakumi = self.db.execute_query(
            "SELECT ienakumi_id, summa, kategorija, datums FROM Ienakumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        return render_template('ienakumi.html', ienakumi=ienakumi, kategorijas=kategorijas)


    def izdevumi(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        kategorijas = ['Pārtika', 'Transports', 'Īre', 'Izklaide', 'Apģērbs', 'Veselība', 'Izglītība', 'Sports', 'Dāvanas, ziedojumi', 'Rēķini', 'Cits']

        if request.method == 'POST':
            summa = request.form['summa']
            kategorija = request.form['kategorija']

            datums = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.db.execute_query(
                "INSERT INTO Izdevumi (user_id, summa, kategorija, datums) VALUES (?, ?, ?, ?)",
                (session['user_id'], summa, kategorija, datums), commit=True)

            flash("Izdevums veiksmīgi pievienots!", "success")
            return redirect(url_for('izdevumi'))

        izdevumi = self.db.execute_query(
            "SELECT izdevumi_id, summa, kategorija, datums FROM Izdevumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)


        return render_template('izdevumi.html', izdevumi=izdevumi, kategorijas=kategorijas)

    def merki(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            nosaukums = request.form['nosaukums']
            summa = request.form['summa']
            kategorija = request.form.get('kategorija')
            periods = request.form['periods']
            
            sasniegts = 0

            self.db.execute_query(
                "INSERT INTO Merki (user_id, nosaukums, summa, sasniegts, kategorija, periods) VALUES (?, ?, ?, ?, ?, ?)",
                (session['user_id'], nosaukums, summa, sasniegts, kategorija, periods), commit=True)
            
            flash("Mērķis veiksmīgi pievienots!", "success")
            return redirect(url_for('merki'))

        merki = self.db.execute_query(
            "SELECT * FROM Merki WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)
        
        return render_template('merki.html', merki=merki)
    
    def delete_ienakumi(self, ienakumi_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        self.db.execute_query(
            "DELETE FROM Ienakumi WHERE user_id = ? AND ienakumi_id = ?",
            (session['user_id'], ienakumi_id), commit=True)

        flash("Ienākums veiksmīgi izdzēsts!", "success")
        return redirect(url_for('ienakumi'))

    def delete_izdevumi(self, izdevumi_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        self.db.execute_query(
            "DELETE FROM Izdevumi WHERE user_id = ? AND izdevumi_id = ?",
            (session['user_id'], izdevumi_id), commit=True)

        flash("Izdevums veiksmīgi izdzēsts!", "success")
        return redirect(url_for('izdevumi'))
    
    def delete_merki(self, merki_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        self.db.execute_query(
            "DELETE FROM Merki WHERE user_id = ? AND merki_id = ?",
            (session['user_id'], merki_id), commit=True)

        flash("Mērķis veiksmīgi izdzēsts!", "success")
        return redirect(url_for('merki')) 
    
    def logout(self):
        session.pop('user_id', None)
        flash("Tu esi izlogojies.", "success")
        return redirect(url_for('login'))

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    app = FinansuApp()
    app.run()