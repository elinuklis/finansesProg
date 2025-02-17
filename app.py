import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
DB_PATH = '/mnt/data/finansesprog.db'

def create_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        lietotajvards = request.form['lietotajvards']
        parole = generate_password_hash(request.form['parole'])
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Lietotajs (lietotajvards, parole) VALUES (?, ?)", (lietotajvards, parole))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        lietotajvards = request.form['lietotajvards']
        parole = request.form['parole']
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, parole FROM Lietotajs WHERE lietotajvards = ?", (lietotajvards,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], parole):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Ienakumi WHERE user_id = ?", (session['user_id'],))
    ienakumi = cursor.fetchall()
    cursor.execute("SELECT * FROM Izdevumi WHERE user_id = ?", (session['user_id'],))
    izdevumi = cursor.fetchall()
    cursor.execute("SELECT * FROM Merki WHERE user_id = ?", (session['user_id'],))
    merki = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', ienakumi=ienakumi, izdevumi=izdevumi, merki=merki)

@app.route('/ienakumi')
def ienakumi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Ienakumi WHERE user_id = ?", (session['user_id'],))
    ienakumi = cursor.fetchall()
    conn.close()
    return render_template('ienakumi.html', ienakumi=ienakumi)

@app.route('/izdevumi')
def izdevumi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Izdevumi WHERE user_id = ?", (session['user_id'],))
    izdevumi = cursor.fetchall()
    conn.close()
    return render_template('izdevumi.html', izdevumi=izdevumi)

@app.route('/merki')
def merki():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Merki WHERE user_id = ?", (session['user_id'],))
    merki = cursor.fetchall()
    conn.close()
    return render_template('merki.html', merki=merki)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
