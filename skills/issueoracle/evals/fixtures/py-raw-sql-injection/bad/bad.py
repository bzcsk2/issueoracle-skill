import sqlite3

def get_user(name):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE name = '{name}'")
    return cur.fetchone()
