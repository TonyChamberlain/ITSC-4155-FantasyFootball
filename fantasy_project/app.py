import os
import sqlite3
from flask import Flask, request, redirect, session, send_from_directory, g, url_for
from flask_bcrypt import Bcrypt
from flask_session import Session

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))
DB_PATH = os.path.join(BASE_DIR, 'users.db')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
# Remember to come back and do this
app.secret_key = 'replace-with-a-strong-random-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
bcrypt = Bcrypt(app)


def get_db():
    db = getattr(g, '_db', None)
    if not db:
        db = g._db = sqlite3.connect(DB_PATH)
        db.execute(
            '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            pw_hash TEXT NOT NULL
            )'''
        )
    return db

@app.teardown_appcontext
def close_db(_):
    db = getattr(g, '_db', None)
    if db:
        db.close()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:filename>')
def static_proxy(filename):
    return app.send_static_file(filename)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username'].strip()
    password = request.form['password']
    if not username or not password:
        return 'Missing fields', 400
    
    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        db = get_db()
        db.execute('INSERT INTO users (username, pw_hash) VALUES (?,?)',
                   (username, pw_hash))
        db.commit()
    except sqlite3.IntegrityError:
        return 'Username Taken', 409
    
    session['user'] = username
    return redirect(url_for('team'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password']
    db = get_db()
    row = db.execute(
        'SELECT pw_hash from users WHERE username=?', (username,)
        ).fetchone()
    if not row or not bcrypt.check_password_hash(row[0], password):
        return 'Invalid credentials', 401
    
    session['user'] = username
    return redirect(url_for('team'))
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login.html')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login.html')
        return f(*args, **kwargs)
    return wrapped

@app.route('/team.html')
@login_required
def team():
    return app.send_static_file('team.html')

if __name__ == '__main__':
    print("Serving frontend from: ", FRONTEND_DIR)
    app.run(debug=True)