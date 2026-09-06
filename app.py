import os
import pymysql
import requests
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

DB_HOST = os.environ.get('DB_HOST', 'REPLACE_WITH_RDS_ENDPOINT')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASS = os.environ.get('DB_PASS', 'REPLACE_WITH_YOUR_PASSWORD')
DB_NAME = os.environ.get('DB_NAME', 'guestbook')

def get_connection():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                            database=DB_NAME, connect_timeout=5)

def init_db():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                message VARCHAR(500)
            )
        """)
    conn.commit()
    conn.close()

def get_instance_id():
    try:
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, timeout=1
        ).text
        return requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token}, timeout=1
        ).text
    except Exception:
        return "unknown (not running on EC2)"

PAGE = """
<h1>Guestbook</h1>
<p><b>Served by instance:</b> {{ instance_id }}</p>
<form method="post" action="/add">
  Name: <input name="name"><br>
  Message: <input name="message"><br>
  <button type="submit">Sign Guestbook</button>
</form>
<hr>
{% for e in entries %}
  <p><b>{{ e[1] }}:</b> {{ e[2] }}</p>
{% endfor %}
"""

@app.route('/')
def index():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM entries ORDER BY id DESC LIMIT 20")
        entries = cur.fetchall()
    conn.close()
    return render_template_string(PAGE, entries=entries, instance_id=get_instance_id())

@app.route('/add', methods=['POST'])
def add():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO entries (name, message) VALUES (%s, %s)",
                     (request.form['name'], request.form['message']))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80)
