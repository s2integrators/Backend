# app/hrmatching/database.py
from mysql.connector import connect, Error
from contextlib import contextmanager

def get_connection():
    try:
        conn = connect(
            host="localhost",
            user="root",
            password="Abid@pc19",   # your password
            database="pythontesting"       # your DB
        )
        return conn
    except Error as e:
        print(f"❌ HR Matching DB Error: {e}")
        return None

@contextmanager
def get_session():
    conn = get_connection()
    if conn is None:
        yield None
        return
    try:
        cursor = conn.cursor(dictionary=True)
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()
