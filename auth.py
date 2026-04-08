import streamlit as st

# Simple credentials - in production use a real auth system
# Add these to your secrets.toml
STAFF_CREDENTIALS = None  # loaded from secrets

def load_credentials():
    try:
        return st.secrets["auth"]["staff_password"]
    except:
        return "gonzagaIT2024"  # fallback default

def login_page():
    st.set_page_config(page_title="GU IT Help Desk - Login", page_icon="🔧", layout="centered")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🦾 Gonzaga University")
        st.markdown("### IT Help Desk")
        st.divider()

        role = st.radio("I am a...", ["Student / Faculty / Staff", "IT Technician"],
                        horizontal=True)

        if role == "Student / Faculty / Staff":
            if st.button("Continue as Student →", type="primary", use_container_width=True):
                st.session_state["role"] = "student"
                st.session_state["logged_in"] = True
                st.rerun()

        else:
            with st.form("staff_login"):
                password = st.text_input("Staff Password", type="password")
                if st.form_submit_button("Login as IT Staff", type="primary", use_container_width=True):
                    if password == load_credentials():
                        st.session_state["role"] = "staff"
                        st.session_state["logged_in"] = True
                        st.rerun()
                    else:
                        st.error("Incorrect password.")

        st.caption("Students: click Continue to submit a support ticket.")


def require_staff():
    """Call at top of any staff-only page."""
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.page_link("Home.py", label="← Back to Login")
        st.stop()
    if st.session_state.get("role") != "staff":
        st.error("⛔ This page is for IT staff only.")
        st.page_link("pages/1_Submit_Ticket.py", label="← Submit a Ticket")
        st.stop()


def require_login():
    """Call at top of any page that needs any login."""
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.page_link("Home.py", label="← Back to Login")
        st.stop()


def logout_button():
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()


def role_badge():
    role = st.session_state.get("role", "")
    if role == "staff":
        st.sidebar.success("👤 IT Staff")
    elif role == "student":
        st.sidebar.info("👤 Student")
