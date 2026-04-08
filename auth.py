import streamlit as st

def load_credentials() -> str:
    try:
        return st.secrets["auth"]["staff_password"]
    except Exception:
        return "gonzagaIT2024"
