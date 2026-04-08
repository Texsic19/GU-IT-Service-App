import streamlit as st
from auth import load_credentials

# ── If already logged in, rerun so app.py redirects ──────────
if st.session_state.get("logged_in"):
    st.rerun()

st.markdown("""
<style>
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

_, center, _ = st.columns([1, 2, 1])
with center:
    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;margin-top:2rem">
        <div style="display:inline-flex;align-items:center;justify-content:center;
                    background:#002147;border-radius:14px;width:64px;height:64px;margin-bottom:1rem">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
                 fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
        </div>
        <h1 style="margin:0;font-size:1.6rem;font-weight:700;color:#002147;letter-spacing:-0.5px">
            Gonzaga University
        </h1>
        <p style="margin:4px 0 0;color:#6b7280;font-size:0.95rem">IT Help Desk Portal</p>
    </div>
    """, unsafe_allow_html=True)

    role = st.radio("I am a...", ["Student / Faculty / Staff", "IT Technician"], horizontal=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if role == "Student / Faculty / Staff":
        st.info("No password needed — click below to submit a support ticket.")
        if st.button("Continue to Submit a Ticket →", type="primary", use_container_width=True):
            st.session_state["role"] = "student"
            st.session_state["logged_in"] = True
            st.rerun()
    else:
        with st.form("staff_login"):
            password = st.text_input("Staff Password", type="password", placeholder="Enter IT staff password")
            if st.form_submit_button("Sign In as IT Staff", type="primary", use_container_width=True):
                if password == load_credentials():
                    st.session_state["role"] = "staff"
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")

    st.markdown("""
    <div style="text-align:center;margin-top:2rem;color:#9ca3af;font-size:0.8rem">
        Gonzaga University · Information Technology Services<br>
        Need help? Call the IT Help Desk at 509-313-5550
    </div>
    """, unsafe_allow_html=True)
