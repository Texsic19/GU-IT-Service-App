import streamlit as st
from auth import load_credentials

st.set_page_config(
    page_title="GU IT Help Desk — Login",
    page_icon="🔧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Hide sidebar and default nav on login page ────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
header { visibility: hidden; }

.login-card {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    border: 1px solid #e5e7eb;
    margin-top: 2rem;
}
.gu-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.25rem;
}
.gu-logo-icon {
    background: #002147;
    border-radius: 10px;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.role-card {
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
    margin-bottom: 0.75rem;
}
.role-card:hover {
    border-color: #002147;
    background: #f8faff;
}
.role-card.selected {
    border-color: #002147;
    background: #eff6ff;
}
</style>
""", unsafe_allow_html=True)

# ── If already logged in, redirect ───────────────────────────
if st.session_state.get("logged_in"):
    if st.session_state.get("role") == "staff":
        st.switch_page("Home.py")
    else:
        st.switch_page("pages/1_Submit_Ticket.py")

# ── Login UI ──────────────────────────────────────────────────
_, center, _ = st.columns([1, 2.5, 1])

with center:
    # Logo + title
    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;margin-top:3rem">
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

    st.markdown("#### Who are you?")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    role = st.radio(
        "Role",
        ["Student / Faculty / Staff", "IT Technician"],
        label_visibility="collapsed"
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if role == "Student / Faculty / Staff":
        st.markdown("""
        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;
                    padding:1rem;margin-bottom:1rem;font-size:0.9rem;color:#0369a1;
                    display:flex;align-items:flex-start;gap:10px">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                 fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                 stroke-linejoin="round" style="margin-top:1px;flex-shrink:0">
                <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
            </svg>
            <span>No password needed. Click below to go straight to the ticket submission form.</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Continue to Submit a Ticket →", type="primary", use_container_width=True):
            st.session_state["role"] = "student"
            st.session_state["logged_in"] = True
            st.switch_page("pages/1_Submit_Ticket.py")

    else:
        with st.form("staff_login_form"):
            password = st.text_input(
                "Staff Password",
                type="password",
                placeholder="Enter your IT staff password"
            )
            submitted = st.form_submit_button(
                "Sign In as IT Staff",
                type="primary",
                use_container_width=True
            )

        if submitted:
            if password == load_credentials():
                st.session_state["role"] = "staff"
                st.session_state["logged_in"] = True
                st.switch_page("Home.py")
            else:
                st.error("Incorrect password. Please try again.")

    st.markdown("""
    <div style="text-align:center;margin-top:2rem;padding-top:1.5rem;
                border-top:1px solid #e5e7eb;color:#9ca3af;font-size:0.8rem">
        Gonzaga University · Information Technology Services<br>
        Need help? Call the IT Help Desk at 509-313-5550
    </div>
    """, unsafe_allow_html=True)
