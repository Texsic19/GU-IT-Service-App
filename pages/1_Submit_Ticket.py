import streamlit as st
from db import run_query, run_insert
from ai_utils import ai_categorize_ticket, ai_suggest_fix
from auth import logout_button, role_badge

st.set_page_config(page_title="Submit a Ticket", page_icon="📝", layout="wide")

# ── Auth gate ─────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.page_link("Home.py", label="← Back to Login")
    st.stop()

role_badge()
logout_button()

st.title("📝 Submit a Support Ticket")
st.markdown("Fill out the form below. Our AI will automatically categorize and prioritize your ticket.")
st.divider()

with st.form("submit_ticket_form", clear_on_submit=True):
    st.subheader("Your Information")
    col1, col2 = st.columns(2)
    with col1:
        submitter_name = st.text_input("Your Full Name *", placeholder="e.g. Alex Zamora")
    with col2:
        submitter_email = st.text_input("Your GU Email *", placeholder="username@zagmail.gonzaga.edu")

    st.subheader("Ticket Details")
    col3, col4 = st.columns(2)
    with col3:
        title    = st.text_input("Issue Title *", placeholder="e.g. Cannot connect to campus WiFi")
        location = st.text_input("Location", placeholder="e.g. Herak 204, Library 3rd floor")
    with col4:
        st.markdown("**AI will auto-detect category & priority** 🤖")
        manual_category = st.selectbox("Category (optional override)",
            ["Auto-detect 🤖", "Network", "Hardware", "Software",
             "Account/Access", "AV Equipment", "Email", "Printing", "General"])
        manual_priority = st.selectbox("Priority (optional override)",
            ["Auto-detect 🤖", "Low", "Medium", "High", "Critical"])

    description = st.text_area("Describe your issue *", height=150,
        placeholder="Describe the problem in detail. Include what you were doing, any error messages, and what you've already tried.")

    submitted = st.form_submit_button("🚀 Submit Ticket", use_container_width=True, type="primary")

if submitted:
    import re
    errors = []
    if not submitter_name.strip():
        errors.append("Your name is required.")
    if not submitter_email.strip():
        errors.append("Your email is required.")
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", submitter_email):
        errors.append("Please enter a valid email address.")
    if not title.strip():
        errors.append("Issue title is required.")
    if not description.strip() or len(description.strip()) < 20:
        errors.append("Please provide more detail in the description (at least 20 characters).")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("🤖 AI is analyzing your ticket..."):
            if manual_category == "Auto-detect 🤖" or manual_priority == "Auto-detect 🤖":
                ai_result     = ai_categorize_ticket(title, description)
                category      = ai_result.get("category", "General") if manual_category == "Auto-detect 🤖" else manual_category
                priority      = ai_result.get("priority", "Medium")  if manual_priority == "Auto-detect 🤖" else manual_priority
                ai_categorized = True
            else:
                category       = manual_category
                priority       = manual_priority
                ai_categorized = False

            ai_fix = ai_suggest_fix(title, description, category)

            ticket_id = run_insert("""
                INSERT INTO tickets
                    (title, description, status, priority, category,
                     submitter_name, submitter_email,
                     ai_suggested_fix, ai_categorized, location)
                VALUES (%s, %s, 'Open', %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (title.strip(), description.strip(), priority, category,
                  submitter_name.strip(), submitter_email.strip().lower(),
                  ai_fix, ai_categorized,
                  location.strip() if location else None))

        st.success(f"✅ Ticket #{ticket_id} submitted successfully!")
        col_a, col_b, col_c = st.columns(3)
        col_a.info(f"**Category:** {category} {'🤖' if ai_categorized else ''}")
        col_b.info(f"**Priority:** {priority} {'🤖' if ai_categorized else ''}")
        col_c.info("**Status:** Open")

        with st.expander("🤖 AI-Suggested Fix (for IT staff reference)", expanded=False):
            st.markdown(ai_fix)
        st.balloons()
