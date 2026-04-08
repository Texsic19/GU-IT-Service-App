import streamlit as st

st.set_page_config(
    page_title="GU IT Help Desk",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Role-based navigation ─────────────────────────────────────
role = st.session_state.get("role")
logged_in = st.session_state.get("logged_in", False)

if not logged_in:
    # Only show login
    pages = [st.Page("pages/login.py", title="Login", icon=":material/login:")]

elif role == "student":
    # Students only see Submit Ticket
    pages = [
        st.Page("pages/submit_ticket.py", title="Submit a Ticket", icon=":material/send:", default=True),
    ]

else:
    # IT Staff see everything except login
    pages = [
        st.Page("pages/dashboard.py",          title="Dashboard",            icon=":material/dashboard:",    default=True),
        st.Page("pages/manage_tickets.py",      title="Manage Tickets",       icon=":material/list:"),
        st.Page("pages/ticket_detail.py",       title="Ticket Detail",        icon=":material/search:"),
        st.Page("pages/manage_users.py",        title="Manage Users",         icon=":material/group:"),
        st.Page("pages/manage_technicians.py",  title="Manage Technicians",   icon=":material/build:"),
        st.Page("pages/tags.py",                title="Tags",                 icon=":material/label:"),
    ]

pg = st.navigation(pages, position="sidebar")

# ── Sidebar footer ────────────────────────────────────────────
if logged_in:
    with st.sidebar:
        st.divider()
        if role == "staff":
            st.markdown(
                '<div style="padding:6px 10px;background:#dcfce7;border-radius:8px;'
                'font-size:0.82rem;color:#166534">🛡️ IT Staff</div>',
                unsafe_allow_html=True
            )
        elif role == "student":
            st.markdown(
                '<div style="padding:6px 10px;background:#dbeafe;border-radius:8px;'
                'font-size:0.82rem;color:#1e40af">🎓 Student</div>',
                unsafe_allow_html=True
            )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

pg.run()
