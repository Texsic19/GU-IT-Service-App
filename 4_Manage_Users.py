import streamlit as st
import re
from db import run_query, run_insert

st.set_page_config(page_title="Manage Users", page_icon="👥", layout="wide")
st.title("👥 Manage Users")
st.markdown("*Add and manage students, staff, and faculty who can submit tickets.*")
st.divider()

# ── Add User Form ─────────────────────────────────────────────
with st.expander("➕ Add New User", expanded=False):
    with st.form("add_user_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First Name *")
            email = st.text_input("Email *", placeholder="username@zagmail.gonzaga.edu")
            department = st.text_input("Department", placeholder="e.g. Computer Science")
        with c2:
            last_name = st.text_input("Last Name *")
            phone = st.text_input("Phone", placeholder="509-555-0100")
            role = st.selectbox("Role *", ["student", "staff", "faculty"])

        if st.form_submit_button("Add User", type="primary"):
            errors = []
            if not first_name.strip(): errors.append("First name is required.")
            if not last_name.strip():  errors.append("Last name is required.")
            if not email.strip():      errors.append("Email is required.")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email): errors.append("Invalid email format.")
            if phone and not re.match(r"^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$", phone.replace(" ", "")):
                errors.append("Phone must be 10 digits (e.g. 509-313-1000).")

            if errors:
                for e in errors: st.error(e)
            else:
                try:
                    run_insert("""
                        INSERT INTO users (first_name, last_name, email, phone, department, role)
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                    """, (first_name.strip(), last_name.strip(), email.strip().lower(),
                          phone.strip() or None, department.strip() or None, role))
                    st.success(f"✅ User {first_name} {last_name} added!")
                    st.rerun()
                except Exception:
                    st.error("Email already exists in the system.")

# ── Search ────────────────────────────────────────────────────
search = st.text_input("🔍 Search users", placeholder="Name, email, or department...")

where = ""
params = []
if search:
    where = "WHERE first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s OR department ILIKE %s"
    params = [f"%{search}%"] * 4

users = run_query(f"SELECT * FROM users {where} ORDER BY last_name, first_name", params or None)
st.markdown(f"**{len(users)} user(s)**")

if not users:
    st.info("No users found.")
    st.stop()

# ── User Table with Edit/Delete ───────────────────────────────
for u in users:
    with st.expander(f"**{u['last_name']}, {u['first_name']}** — {u['email']} · {u['role'].title()}"):
        col_form, col_del = st.columns([4, 1])

        with col_form:
            with st.form(f"edit_user_{u['id']}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_first = st.text_input("First Name", value=u["first_name"])
                    e_email = st.text_input("Email", value=u["email"])
                    e_dept  = st.text_input("Department", value=u["department"] or "")
                with ec2:
                    e_last  = st.text_input("Last Name", value=u["last_name"])
                    e_phone = st.text_input("Phone", value=u["phone"] or "")
                    e_role  = st.selectbox("Role", ["student", "staff", "faculty"],
                                           index=["student", "staff", "faculty"].index(u["role"]))
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    errors = []
                    if not e_first.strip(): errors.append("First name required.")
                    if not e_last.strip():  errors.append("Last name required.")
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", e_email): errors.append("Invalid email.")
                    if errors:
                        for e in errors: st.error(e)
                    else:
                        try:
                            run_query("""
                                UPDATE users SET first_name=%s, last_name=%s, email=%s,
                                phone=%s, department=%s, role=%s WHERE id=%s
                            """, (e_first.strip(), e_last.strip(), e_email.strip().lower(),
                                  e_phone.strip() or None, e_dept.strip() or None, e_role, u["id"]),
                                fetch=False)
                            st.success("Updated!")
                            st.rerun()
                        except Exception:
                            st.error("Email already taken.")

        with col_del:
            st.markdown("###")
            if st.button("🗑️ Delete", key=f"del_user_{u['id']}"):
                st.session_state[f"confirm_del_user_{u['id']}"] = True
            if st.session_state.get(f"confirm_del_user_{u['id']}"):
                st.warning("Delete this user?")
                if st.button("Confirm", key=f"confirm_user_{u['id']}", type="primary"):
                    run_query("DELETE FROM users WHERE id = %s", (u["id"],), fetch=False)
                    st.rerun()
                if st.button("Cancel", key=f"cancel_user_{u['id']}"):
                    st.session_state[f"confirm_del_user_{u['id']}"] = False
                    st.rerun()
