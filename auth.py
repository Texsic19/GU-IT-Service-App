import streamlit as st


def load_credentials() -> str:
    try:
        return st.secrets["auth"]["staff_password"]
    except Exception:
        return "gonzagaIT2024"


def require_staff():
    """Redirect to login if not authenticated as staff."""
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/0_Login.py")
        st.stop()
    if st.session_state.get("role") != "staff":
        st.error("⛔ This page is for IT staff only.")
        st.page_link("pages/1_Submit_Ticket.py", label="← Submit a Ticket")
        st.stop()


def require_login():
    """Redirect to login if not authenticated at all."""
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/0_Login.py")
        st.stop()


def logout_button():
    from icons import icon
    if st.sidebar.button(
        f"Logout",
        key="logout_btn",
        help="Sign out"
    ):
        st.session_state.clear()
        st.switch_page("pages/0_Login.py")


def role_badge():
    from icons import icon
    role = st.session_state.get("role", "")
    if role == "staff":
        st.sidebar.markdown(
            f'<div style="padding:8px 12px;background:#dcfce7;border-radius:8px;'
            f'font-size:0.85em;color:#166534;display:flex;align-items:center;gap:6px;margin-bottom:8px">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>'
            f'IT Staff</div>',
            unsafe_allow_html=True
        )
    elif role == "student":
        st.sidebar.markdown(
            f'<div style="padding:8px 12px;background:#dbeafe;border-radius:8px;'
            f'font-size:0.85em;color:#1e40af;display:flex;align-items:center;gap:6px;margin-bottom:8px">'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
            f'Student</div>',
            unsafe_allow_html=True
        )
