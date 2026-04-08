import psycopg2
import streamlit as st

def get_connection():
    return psycopg2.connect(st.secrets["database"]["DB_URL"])

def run_query(sql, params=None, fetch=True):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch:
                cols = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return [dict(zip(cols, row)) for row in rows]
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()

def run_insert(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.fetchone()[0] if cur.description else None
    finally:
        conn.close()
