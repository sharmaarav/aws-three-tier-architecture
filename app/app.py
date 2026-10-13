from flask import Flask, jsonify, request, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "legacydb")
DB_USER = os.getenv("DB_USER", "legacyuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "legacypass")

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/db-health")
def db_health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1 AS ok;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"database": "reachable", "result": result["ok"]}), 200
    except Exception as exc:
        return jsonify({"database": "unreachable", "error": str(exc)}), 500

@app.route("/api/customers", methods=["GET"])
def customers():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, created_at FROM customers ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route("/api/customers", methods=["POST"])
def add_customer():
    payload = request.get_json(force=True)
    name = payload.get("name")
    email = payload.get("email")
    if not name or not email:
        return jsonify({"error": "name and email are required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO customers (name, email) VALUES (%s, %s) "
        "RETURNING id, name, email, created_at;",
        (name, email),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(row), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
