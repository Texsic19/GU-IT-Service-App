import streamlit as st
import re
from db import run_insert
from ai_utils import ai_categorize_ticket
from icons import icon_header, icon_text

st.markdown(icon_header("send", "Submit a Support Ticket", level=1), unsafe_allow_html=True)
st.markdown(
    f'<p style="color:#6b7280;margin-top:0">'
    f'{icon_text("sparkles", "Our AI will automatically categorize and prioritize your ticket.", 14, "#6b7280")}'
    f'</p>', unsafe_allow_html=True)
st.divider()

with st.form("submit_ticket_form", clear_on_submit=True):
    st.markdown(icon_header("user", "Your Information", level=3), unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        submitter_name = st.text_input("Your Full Name *", placeholder="e.g. Alex Zamora")
    with col2:
        submitter_email = st.text_input("Your GU Email *", placeholder="username@zagmail.gonzaga.edu")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(icon_header("ticket", "Ticket Details", level=3), unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        title    = st.text_input("Issue Title *", placeholder="e.g. Cannot connect to campus WiFi")
        location = st.text_input("Location", placeholder="e.g. Herak 204, Library 3rd floor")
    with col4:
        st.markdown(
            f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
            f'padding:10px 14px;font-size:0.85rem;color:#166534;margin-bottom:8px">'
            f'{icon_text("bot", "AI will auto-detect category & priority", 14, "#166534")}'
            f'</div>', unsafe_allow_html=True)
        manual_category = st.selectbox("Category (optional override)",
            ["Auto-detect 🤖", "Network", "Hardware", "Software",
             "Account/Access", "AV Equipment", "Email", "Printing", "General"])
        manual_priority = st.selectbox("Priority (optional override)",
            ["Auto-detect 🤖", "Low", "Medium", "High", "Critical"])

    description = st.text_area("Describe your issue *", height=150,
        placeholder="Describe the problem in detail. Include what you were doing, any error messages, and what you've already tried.")

    submitted = st.form_submit_button("Submit Ticket", use_container_width=True, type="primary")

if submitted:
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
        errors.append("Please provide more detail (at least 20 characters).")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("AI is analyzing your ticket..."):
            if manual_category == "Auto-detect 🤖" or manual_priority == "Auto-detect 🤖":
                ai_result      = ai_categorize_ticket(title, description)
                category       = ai_result.get("category", "General") if manual_category == "Auto-detect 🤖" else manual_category
                priority       = ai_result.get("priority", "Medium")  if manual_priority == "Auto-detect 🤖" else manual_priority
                ai_categorized = True
            else:
                category, priority, ai_categorized = manual_category, manual_priority, False

            ticket_id = run_insert("""
                INSERT INTO tickets
                    (title, description, status, priority, category,
                     submitter_name, submitter_email, ai_suggested_fix, ai_categorized, location)
                VALUES (%s, %s, 'Open', %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (title.strip(), description.strip(), priority, category,
                  submitter_name.strip(), submitter_email.strip().lower(),
                  None, ai_categorized, location.strip() if location else None))

        st.markdown(
            f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:1.25rem;margin-bottom:1rem">'
            f'{icon_text("check-circle", f"Ticket #{ticket_id} submitted successfully!", 20, "#15803d")}'
            f'</div>', unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(
                f'<div style="background:#eff6ff;border-radius:8px;padding:12px;font-size:0.9rem">'
                f'{icon_text("tag", f"Category: {category}", 14, "#1d4ed8")} {"🤖" if ai_categorized else ""}'
                f'</div>', unsafe_allow_html=True)
        with col_b:
            st.markdown(
                f'<div style="background:#fefce8;border-radius:8px;padding:12px;font-size:0.9rem">'
                f'{icon_text("zap", f"Priority: {priority}", 14, "#854d0e")} {"🤖" if ai_categorized else ""}'
                f'</div>', unsafe_allow_html=True)
        with col_c:
            st.markdown(
                f'<div style="background:#f0fdf4;border-radius:8px;padding:12px;font-size:0.9rem">'
                f'{icon_text("clock", "Status: Open", 14, "#15803d")}'
                f'</div>', unsafe_allow_html=True)
        st.balloons()
