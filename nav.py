"""
Injects CSS to hide staff-only nav items from students.
Streamlit renders sidebar nav as <li> items containing <a> tags whose
href matches the page filename. We target those by the page slug.
"""
import streamlit as st

STAFF_PAGES = [
    "2_manage_tickets",
    "3_ticket_detail",
    "4_manage_users",
    "5_manage_technicians",
    "6_tags",
]

def apply_nav_visibility():
    """Call once per page after set_page_config. Hides staff pages for students."""
    role = st.session_state.get("role", "")
    if role == "student":
        # Build a CSS rule hiding each staff page link in the sidebar
        selectors = ", ".join(
            f'[data-testid="stSidebarNav"] a[href*="{slug}"]'
            for slug in STAFF_PAGES
        )
        # Also hide the parent <li> so there's no gap
        li_selectors = ", ".join(
            f'[data-testid="stSidebarNav"] li:has(a[href*="{slug}"])'
            for slug in STAFF_PAGES
        )
        st.markdown(
            f"<style>{selectors} {{ display: none !important; }}"
            f"{li_selectors} {{ display: none !important; }}</style>",
            unsafe_allow_html=True,
        )
    # Always hide the login page from the nav (it's an implementation detail)
    st.markdown(
        '<style>'
        '[data-testid="stSidebarNav"] a[href*="0_login"] { display: none !important; }'
        '[data-testid="stSidebarNav"] li:has(a[href*="0_login"]) { display: none !important; }'
        '</style>',
        unsafe_allow_html=True,
    )
