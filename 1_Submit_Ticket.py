import streamlit as st
from db import run_query, run_insert
from ai_utils import ai_categorize_ticket, ai_suggest_fix

st.set_page_config(page_title="Submit a Ticket", page_icon="📝", layout="wide")
st.title("📝 Submit a Support Ticket")
st.markdown("Fill out the form below and our AI will automatically categorize and prioritize your ticket.")
st.divider()

# ── Load users for dropdown ──────────────────────────────────
users = run_query("SELECT id, first_name || ' ' || last_name || ' (' || email || ')' AS label FROM users ORDER BY last_name")
user_map = {u["label"]: u["id"] for u in users}

if not users:
    st.warning("No users found. Please add users in **Manage Users** first.")
    st.stop()

with st.form("submit_ticket_form", clear_on_submit=True):
    st.subheader("Your Information")
    selected_user = st.selectbox("Select Your Name *", options=list(user_map.keys()))

    st.subheader("Ticket Details")
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Issue Title *", placeholder="e.g. Cannot connect to campus WiFi")
        location = st.text_input("Location", placeholder="e.g. Herak 204, Library 3rd floor")
    with col2:
        st.markdown("**AI will auto-detect category & priority** 🤖")
        st.caption("You can also set them manually if you prefer.")
        manual_category = st.selectbox("Category (optional override)",
            ["Auto-detect 🤖", "Network", "Hardware", "Software",
             "Account/Access", "AV Equipment", "Email", "Printing", "General"])
        manual_priority = st.selectbox("Priority (optional override)",
            ["Auto-detect 🤖", "Low", "Medium", "High", "Critical"])

    description = st.text_area("Describe your issue *", height=150,
        placeholder="Please describe the problem in detail. Include what you were doing when the issue occurred, any error messages, and what you have already tried.")

    submitted = st.form_submit_button("🚀 Submit Ticket", use_container_width=True, type="primary")

if submitted:
    # Validation
    errors = []
    if not title.strip():
        errors.append("Issue title is required.")
    if not description.strip():
        errors.append("Description is required.")
    if len(description.strip()) < 20:
        errors.append("Please provide more detail in the description (at least 20 characters).")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("🤖 AI is analyzing your ticket..."):
            # AI categorization
            if manual_category == "Auto-detect 🤖" or manual_priority == "Auto-detect 🤖":
                ai_result = ai_categorize_ticket(title, description)
                category = ai_result.get("category", "General") if manual_category == "Auto-detect 🤖" else manual_category
                priority = ai_result.get("priority", "Medium") if manual_priority == "Auto-detect 🤖" else manual_priority
                ai_categorized = True
            else:
                category = manual_category
                priority = manual_priority
                ai_categorized = False

            # AI fix suggestion
            ai_fix = ai_suggest_fix(title, description, category)

            # Insert ticket
            ticket_id = run_insert("""
                INSERT INTO tickets
                    (title, description, status, priority, category,
                     submitter_id, ai_suggested_fix, ai_categorized, location)
                VALUES (%s, %s, 'Open', %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (title.strip(), description.strip(), priority, category,
                  user_map[selected_user], ai_fix, ai_categorized,
                  location.strip() if location else None))

        st.success(f"✅ Ticket #{ticket_id} submitted successfully!")

        col_a, col_b, col_c = st.columns(3)
        col_a.info(f"**Category:** {category} {'🤖' if ai_categorized else ''}")
        col_b.info(f"**Priority:** {priority} {'🤖' if ai_categorized else ''}")
        col_c.info(f"**Status:** Open")

        with st.expander("🤖 AI-Suggested Fix (visible to IT staff)", expanded=False):
            st.markdown(ai_fix)

        st.balloons()
