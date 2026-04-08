import os

import psycopg2
import streamlit as st


def _get_db_url() -> str:
    s = st.secrets
    try:
        return s["database"]["DB_URL"]
    except (KeyError, TypeError):
        pass
    try:
        return s["DB_URL"]
    except KeyError:
        pass
    url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL")
    if url:
        return url
    raise KeyError(
        'database / DB_URL — add [database] with DB_URL to Secrets '
        "(see .streamlit/secrets.toml.example). On Streamlit Cloud, paste TOML "
        "under App settings → Secrets; deployed apps do not read repo secrets.toml."
    )


def get_connection():
    return psycopg2.connect(_get_db_url())

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
