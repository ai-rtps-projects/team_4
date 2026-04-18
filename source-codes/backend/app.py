from flask import Flask, request, jsonify, session, g
import sqlite3, os, re
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"
DATABASE = "database.db"

# ---------------- DATABASE ----------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT
    )
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        doctor TEXT,
        date TEXT,
        slot TEXT
    )
    """)
    db.commit()

# ---------------- AUTH ----------------
@app.post("/register")
def register():
    data = request.json
    db = get_db()

    try:
        db.execute("INSERT INTO users(name,email,phone,password) VALUES (?,?,?,?)",
                   (data['name'], data['email'], data['phone'],
                    generate_password_hash(data['password'])))
        db.commit()
        return jsonify({"msg": "Registered"})
    except:
        return jsonify({"error": "User exists"}), 400


@app.post("/login")
def login():
    data = request.json
    db = get_db()

    user = db.execute("SELECT * FROM users WHERE email=?",
                      (data['email'],)).fetchone()

    if user and check_password_hash(user['password'], data['password']):
        session['user'] = user['id']
        return jsonify({"msg": "Login success"})
    return jsonify({"error": "Invalid"}), 401


# ---------------- CHATBOT ----------------
def detect_intent(msg):
    msg = msg.lower()
    if "book" in msg:
        return "booking"
    if "doctor" in msg:
        return "availability"
    return "general"

@app.post("/chat")
def chat():
    data = request.json
    msg = data.get("message", "")

    intent = detect_intent(msg)

    if intent == "booking":
        return jsonify({"reply": "Please provide doctor name and date"})
    elif intent == "availability":
        return jsonify({"reply": "Doctors available: Cardiologist, Dentist"})
    else:
        return jsonify({"reply": "I can help you book appointments 😊"})


# ---------------- APPOINTMENT ----------------
@app.post("/appointment")
def book():
    data = request.json
    db = get_db()

    db.execute("INSERT INTO appointments(name,phone,doctor,date,slot) VALUES (?,?,?,?,?)",
               (data['name'], data['phone'], data['doctor'],
                data['date'], data['slot']))
    db.commit()

    return jsonify({"msg": "Appointment booked"})


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
