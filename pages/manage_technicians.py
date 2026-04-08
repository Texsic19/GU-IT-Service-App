import streamlit as st
import re
from db import run_query, run_insert
from icons import icon_header, icon_text

st.markdown(icon_header("wrench", "Manage Technicians", level=1), unsafe_allow_html=True)
st.markdown('<p style="color:#6b7280;margin-top:0">Add and manage IT desk workers.</p>', unsafe_allow_html=True)
st.divider()

with st.expander("Add New Technician", expanded=False):
    with st.form("add_tech_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            first_name     = st.text_input("First Name *")
            email          = st.text_input("Email *", placeholder="username@gonzaga.edu")
            specialization = st.text_input("Specialization", placeholder="e.g. Network & Infrastructure")
        with c2:
            last_name = st.text_input("Last Name *")
            phone     = st.text_input("Phone", placeholder="509-313-1000")
            is_active = st.checkbox("Active", value=True)
        if st.form_submit_button("Add Technician", type="primary"):
            errors = []
            if not first_name.strip(): errors.append("First name required.")
            if not last_name.strip():  errors.append("Last name required.")
            if not email.strip():      errors.append("Email required.")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email): errors.append("Invalid email.")
            if phone and not re.match(r"^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$", phone.replace(" ","")):
                errors.append("Phone must be 10 digits.")
            if errors:
                for e in errors: st.error(e)
            else:
                try:
                    run_insert("INSERT INTO technicians (first_name,last_name,email,phone,specialization,is_active) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                        (first_name.strip(), last_name.strip(), email.strip().lower(), phone.strip() or None, specialization.strip() or None, is_active))
                    st.success(f"Technician {first_name} {last_name} added!")
                    st.rerun()
                except Exception:
                    st.error("Email already exists.")

search = st.text_input("Search technicians")
where, params = "", []
if search:
    where = "WHERE first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s OR specialization ILIKE %s"
    params = [f"%{search}%"] * 4

techs = run_query(f"SELECT * FROM technicians {where} ORDER BY last_name, first_name", params or None)
tech_stats = {r["assigned_tech_id"]: r for r in run_query("""
    SELECT assigned_tech_id,
        COUNT(*) FILTER (WHERE status NOT IN ('Resolved','Closed')) AS open_count,
        COUNT(*) AS total_count
    FROM tickets WHERE assigned_tech_id IS NOT NULL GROUP BY assigned_tech_id
""")}
st.markdown(f'<p style="font-size:0.9rem;color:#6b7280">{icon_text("wrench", f"{len(techs)} technician(s)", 14, "#6b7280")}</p>', unsafe_allow_html=True)

for tc in techs:
    stats = tech_stats.get(tc["id"], {})
    label = f"{tc['last_name']}, {tc['first_name']} — {tc.get('specialization') or 'General IT'}  |  {'Active' if tc['is_active'] else 'Inactive'}  |  {stats.get('open_count',0)} open / {stats.get('total_count',0)} total"
    with st.expander(label):
        col_form, col_del = st.columns([4,1])
        with col_form:
            with st.form(f"edit_tech_{tc['id']}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_first = st.text_input("First Name", value=tc["first_name"])
                    e_email = st.text_input("Email", value=tc["email"])
                    e_spec  = st.text_input("Specialization", value=tc["specialization"] or "")
                with ec2:
                    e_last   = st.text_input("Last Name", value=tc["last_name"])
                    e_phone  = st.text_input("Phone", value=tc["phone"] or "")
                    e_active = st.checkbox("Active", value=tc["is_active"])
                if st.form_submit_button("Save Changes", type="primary"):
                    errors = []
                    if not e_first.strip(): errors.append("First name required.")
                    if not e_last.strip():  errors.append("Last name required.")
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", e_email): errors.append("Invalid email.")
                    if errors:
                        for e in errors: st.error(e)
                    else:
                        try:
                            run_query("UPDATE technicians SET first_name=%s,last_name=%s,email=%s,phone=%s,specialization=%s,is_active=%s WHERE id=%s",
                                (e_first.strip(), e_last.strip(), e_email.strip().lower(), e_phone.strip() or None, e_spec.strip() or None, e_active, tc["id"]), fetch=False)
                            st.success("Updated!")
                            st.rerun()
                        except Exception:
                            st.error("Email already taken.")
        with col_del:
            st.markdown("###")
            if st.button("Delete", key=f"del_tech_{tc['id']}"):
                st.session_state[f"confirm_del_tech_{tc['id']}"] = True
            if st.session_state.get(f"confirm_del_tech_{tc['id']}"):
                st.warning("Delete?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Confirm", key=f"confirm_tech_{tc['id']}", type="primary"):
                        run_query("DELETE FROM technicians WHERE id=%s", (tc["id"],), fetch=False)
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"cancel_tech_{tc['id']}"):
                        st.session_state[f"confirm_del_tech_{tc['id']}"] = False
                        st.rerun()
