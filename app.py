import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import requests

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
        self.app.add_url_rule('/update_progress/<int:merki_id>', 'update_progress', self.update_progress, methods=['POST'])
        self.app.add_url_rule('/check_and_update_merki', 'check_and_update_merki', self.check_and_update_merkus)

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

        # Ienākumu/izdevumu un mērķu dati
        ienakumi = self.db.execute_query(
            "SELECT ienakumi_id, summa, kategorija, datums FROM Ienakumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)
        izdevumi = self.db.execute_query(
            "SELECT izdevumi_id, summa, kategorija, datums FROM Izdevumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        ienakumu_kopsumma = sum(float(ienakums[1]) for ienakums in ienakumi) if ienakumi else 0
        izdevumu_kopsumma = sum(float(izdevums[1]) for izdevums in izdevumi) if izdevumi else 0
        atlikums = ienakumu_kopsumma - izdevumu_kopsumma

        merki = self.db.execute_query(
            "SELECT merki_id, nosaukums, summa, pasreizeja_summa, sasniegts, kategorija, periods FROM merki WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        # Atļautās valūtas
        target_currencies = ['USD', 'GBP', 'JPY']
        valutas_kursi = {}
        konvertetie_atlikumi = {}
        api_key = "39c34f01ecdae02f92868c0cf25a1f28"

        for currency in target_currencies:
            try:
                url = f"http://data.fixer.io/api/latest?access_key={api_key}&base=EUR&symbols={currency}"
                response = requests.get(url)
                data = response.json()

                # Ja API atbilde satur kursus, pievieno tos
                if "rates" in data:
                    kurss = data["rates"].get(currency, None)
                    if kurss:
                        valutas_kursi[currency] = kurss
                        konvertetie_atlikumi[currency] = round(atlikums * kurss, 2)
                    else:
                        flash(f"Kļūda saņemot kursu uz {currency}", "warning")
                else:
                    flash(f"Kļūda ielādējot kursu uz {currency}: {data.get('error', 'Nezināma kļūda')}", "warning")
            except Exception as e:
                flash(f"Kļūda ielādējot kursu uz {currency}: {e}", "warning")
                valutas_kursi[currency] = None
                konvertetie_atlikumi[currency] = None

        # Iegūst izvēlēto valūtu no dropdown
        selected_currency = request.args.get('valuta', 'USD')

        valutu_simboli = {
            'USD': '$',
            'GBP': '£',
            'JPY': '¥',
            'EUR': '€'
        }
        valutas_simbols = valutu_simboli.get(selected_currency, '')

        return render_template(
            'dashboard.html',
            ienakumi=ienakumi,
            izdevumi=izdevumi,
            merki=merki,
            ienakumu_kopsumma=ienakumu_kopsumma,
            izdevumu_kopsumma=izdevumu_kopsumma,
            atlikums=atlikums,
            valutas_kursi=valutas_kursi,
            konvertetie_atlikumi=konvertetie_atlikumi,
            selected_currency=selected_currency,
            valutas_simbols=valutas_simbols
        )
    

    def ienakumi(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        kategorijas = ['Alga', 'Pārdošana', 'Pabalsts', 'Dāvana', 'Nodokļu atmaksas', 'Investīciju ienākumi', 'Cits']

        merki = self.db.execute_query(
            "SELECT merki_id, nosaukums FROM merki WHERE user_id = ? AND tips != 'Tēriņu ierobežojums'",
            (session['user_id'],), fetch_all=True
        )

        if request.method == 'POST':
            try:
                summa = round(float(request.form['summa']), 2)
            except ValueError:
                flash("Lūdzu ievadi derīgu skaitli summas laukā.", "danger")
                return redirect(url_for('ienakumi'))

            kategorija = request.form['kategorija']
            datums = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Pievieno ienākumu
            merki_id = request.form.get('merki_id')
            if merki_id == "none":
                merki_id = None
            else:
                merki_id = int(merki_id)  # konvertē uz int tikai ja nav none

            self.db.execute_query(
                "INSERT INTO Ienakumi (user_id, summa, kategorija, datums, merki_id) VALUES (?, ?, ?, ?, ?)",
                (session['user_id'], summa, kategorija, datums, merki_id), commit=True)

            # Ja lietotājs izvēlējies mērķi
            merki_id = request.form.get('merki_id')
            if merki_id and merki_id != "none":
                try:
                    merki_id = int(merki_id)
                    self.db.execute_query(
                        "UPDATE merki SET pasreizeja_summa = pasreizeja_summa + ? WHERE merki_id = ? AND user_id = ?",
                        (summa, merki_id, session['user_id']),
                        commit=True
                    )
                except ValueError:
                    flash("Nederīgs mērķa ID.", "danger")

            self.check_and_update_merkus()

            flash("Ienākums veiksmīgi pievienots!", "success")
            return redirect(url_for('ienakumi'))

        ienakumi = self.db.execute_query(
            "SELECT ienakumi_id, summa, kategorija, datums FROM Ienakumi WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        return render_template('ienakumi.html', ienakumi=ienakumi, kategorijas=kategorijas, merki=merki)


    def izdevumi(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # kategorijas kuras var izvēlēties
        kategorijas = ['Pārtika', 'Transports', 'Īre', 'Izklaide', 'Apģērbs', 'Veselība', 'Izglītība', 'Sports', 'Dāvanas, ziedojumi', 'Rēķini', 'Cits']
        
        merki = self.db.execute_query(
            "SELECT merki_id, nosaukums FROM Merki WHERE user_id = ?",
            (session['user_id'],), fetch_all=True
        )

        if request.method == 'POST':
            summa = request.form['summa']
            kategorija = request.form['kategorija']
            merki_id = request.form['merki_id']  # Ja ir izvēlēts mērķis

            if merki_id == "none":
                merki_id = None
            else:
                merki_id = int(merki_id)

            datums = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


            self.db.execute_query(
                "INSERT INTO Izdevumi (user_id, summa, kategorija, datums, merki_id) VALUES (?, ?, ?, ?, ?)",
                (session['user_id'], summa, kategorija, datums, merki_id), commit=True)


            if merki_id:
                self.db.execute_query(
                    "UPDATE Merki SET pasreizeja_summa = pasreizeja_summa + ? WHERE merki_id = ? AND user_id = ?",
                    (summa, merki_id, session['user_id']),
                    commit=True
                )

            flash("Izdevums veiksmīgi pievienots!", "success")
            return redirect(url_for('izdevumi'))


        izdevumi = self.db.execute_query(
            "SELECT Izdevumi.izdevumi_id, Izdevumi.summa, Izdevumi.kategorija, Izdevumi.datums, Merki.nosaukums AS merks "
            "FROM Izdevumi "
            "LEFT JOIN Merki ON Izdevumi.merki_id = Merki.merki_id "
            "WHERE Izdevumi.user_id = ?",
            (session['user_id'],), fetch_all=True
)


        return render_template('izdevumi.html', izdevumi=izdevumi, kategorijas=kategorijas, merki=merki)

    def merki(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            tips = request.form['goal_type']
            nosaukums = request.form['nosaukums']
            summa = float(request.form['summa'])
            periods = request.form['periods']

            if tips == "Tēriņu ierobežojums":
                kategorija = request.form['category']
            else:
                kategorija = None

            sasniegts = 0
            pasreizeja_summa = 0 

            self.db.execute_query(
                "INSERT INTO merki (user_id, nosaukums, summa, pasreizeja_summa, sasniegts, kategorija, periods, tips) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session['user_id'], nosaukums, summa, pasreizeja_summa, sasniegts, kategorija, periods, tips),
                commit=True
            )

            flash("Mērķis veiksmīgi pievienots!", "success")
            return redirect(url_for('merki'))

        merki = self.db.execute_query(
            "SELECT merki_id, nosaukums, summa, pasreizeja_summa, sasniegts, kategorija, periods, tips FROM merki WHERE user_id = ?",
            (session['user_id'],), fetch_all=True
        )

        return render_template('merki.html', merki=merki)
    
    def check_and_update_merkus(self):
        merki = self.db.execute_query(
            "SELECT merki_id, summa, pasreizeja_summa FROM merki WHERE user_id = ?",
            (session['user_id'],), fetch_all=True)

        for merks in merki:
            if merks[2] >= merks[1]:
                self.db.execute_query(
                    "UPDATE merki SET sasniegts = 1 WHERE merki_id = ?",
                    (merks[0],), commit=True)

    def delete_ienakumi(self, ienakumi_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))


        ienakums = self.db.execute_query(
            "SELECT summa, merki_id FROM Ienakumi WHERE user_id = ? AND ienakumi_id = ?",
            (session['user_id'], ienakumi_id), fetch_one=True)

        if ienakums:
            summa, merki_id = ienakums


            if merki_id:
                self.db.execute_query(
                    "UPDATE merki SET pasreizeja_summa = pasreizeja_summa - ? WHERE merki_id = ? AND user_id = ?",
                    (summa, merki_id, session['user_id']),
                    commit=True
                )


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
            "DELETE FROM merki WHERE user_id = ? AND merki_id = ?",
            (session['user_id'], merki_id), commit=True)

        flash("Mērķis veiksmīgi izdzēsts!", "success")
        return redirect(url_for('merki')) 
    
    def update_progress(self, merki_id):
        if 'user_id' not in session:
            flash("Jums jābūt pieslēgušamies!", "danger")
            return redirect(url_for('login'))


        try:
            summa = float(request.form.get('summa', 0))  
            progress_amount = float(request.form.get('progress_amount', 0)) 
        except ValueError:
            flash("Ievadiet derīgu skaitli!", "danger")
            return redirect(url_for('merki'))


        if progress_amount <= 0:
            flash("Progresam jābūt lielākam par nulli!", "danger")
            return redirect(url_for('merki'))

        # Atjaunina pašreizējo summu
        self.db.execute_query(
            "UPDATE merki SET pasreizeja_summa = pasreizeja_summa + ? WHERE merki_id = ? AND user_id = ?",
            (progress_amount, merki_id, session['user_id']),
            commit=True
        )

        # Pārbauda, vai mērķis ir sasniegts
        self.db.execute_query(
            "UPDATE Merki SET sasniegts = 1 WHERE merki_id = ? AND pasreizeja_summa >= summa",
            (merki_id,),
            commit=True
        )

        flash("Progress  atjaunināts!", "success")
        return redirect(url_for('merki'))

    
    def logout(self):
        session.pop('user_id', None)
        flash("Tu esi izlogojies.", "success")
        return redirect(url_for('login'))

    def run(self):
        self.app.run(debug=True)

    @property
    def flask_app(self):
        return self.app

app = FinansuApp().flask_app

if __name__ == '__main__':
    app.run(debug=True)

