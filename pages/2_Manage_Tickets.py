import streamlit as st
import pandas as pd
from db import run_query, run_insert

st.set_page_config(page_title="Manage Tickets", page_icon="🗂️", layout="wide")
st.title("🗂️ Manage Tickets")
st.markdown("*IT Staff View — Search, filter, assign, and update ticket status.*")
st.divider()

# ── Filters ──────────────────────────────────────────────────
with st.expander("🔍 Search & Filter", expanded=True):
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        search = st.text_input("Search by title or description", placeholder="e.g. wifi, password...")
    with fc2:
        filter_status = st.multiselect("Status", ["Open", "In Progress", "Resolved", "Closed"],
                                       default=["Open", "In Progress"])
    with fc3:
        filter_priority = st.multiselect("Priority", ["Critical", "High", "Medium", "Low"])
    with fc4:
        filter_category = st.multiselect("Category",
            ["Network", "Hardware", "Software", "Account/Access",
             "AV Equipment", "Email", "Printing", "General"])

# ── Build query ───────────────────────────────────────────────
where_clauses = []
params = []

if search:
    where_clauses.append("(t.title ILIKE %s OR t.description ILIKE %s)")
    params += [f"%{search}%", f"%{search}%"]
if filter_status:
    where_clauses.append(f"t.status = ANY(%s)")
    params.append(filter_status)
if filter_priority:
    where_clauses.append(f"t.priority = ANY(%s)")
    params.append(filter_priority)
if filter_category:
    where_clauses.append(f"t.category = ANY(%s)")
    params.append(filter_category)

where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

tickets = run_query(f"""
    SELECT
        t.id, t.title, t.category, t.priority, t.status,
        u.first_name || ' ' || u.last_name AS submitter,
        COALESCE(tech.first_name || ' ' || tech.last_name, 'Unassigned') AS technician,
        t.ai_categorized,
        t.created_at::date AS submitted,
        t.location
    FROM tickets t
    LEFT JOIN users u ON t.submitter_id = u.id
    LEFT JOIN technicians tech ON t.assigned_tech_id = tech.id
    {where_sql}
    ORDER BY
        CASE t.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2
            WHEN 'Medium' THEN 3 ELSE 4 END,
        t.created_at DESC
""", params if params else None)

st.markdown(f"**{len(tickets)} ticket(s) found**")

if not tickets:
    st.info("No tickets match your filters.")
    st.stop()

# ── Ticket rows ───────────────────────────────────────────────
PRIORITY_COLORS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
STATUS_COLORS   = {"Open": "🔵", "In Progress": "🟣", "Resolved": "✅", "Closed": "⬛"}

for t in tickets:
    p_icon = PRIORITY_COLORS.get(t["priority"], "⚪")
    s_icon = STATUS_COLORS.get(t["status"], "⚪")
    ai_badge = " 🤖" if t["ai_categorized"] else ""
    loc_str  = f" · 📍 {t['location']}" if t["location"] else ""

    with st.expander(
        f"{p_icon} **#{t['id']}** — {t['title']}  |  {s_icon} {t['status']}  |  {t['category']}{ai_badge}{loc_str}"
    ):
        col_info, col_actions = st.columns([2, 1])

        with col_info:
            st.markdown(f"**Submitter:** {t['submitter']}  \n"
                        f"**Assigned To:** {t['technician']}  \n"
                        f"**Priority:** {t['priority']}  \n"
                        f"**Submitted:** {t['submitted']}")
            if st.button("🔍 View Full Ticket", key=f"view_{t['id']}"):
                st.session_state["view_ticket_id"] = t["id"]
                st.switch_page("pages/2_Ticket_Detail.py")

        with col_actions:
            techs = run_query("SELECT id, first_name || ' ' || last_name AS name FROM technicians WHERE is_active = TRUE ORDER BY last_name")
            tech_map = {"Unassigned": None}
            tech_map.update({tc["name"]: tc["id"] for tc in techs})

            new_status = st.selectbox("Update Status", ["Open", "In Progress", "Resolved", "Closed"],
                                      index=["Open", "In Progress", "Resolved", "Closed"].index(t["status"]),
                                      key=f"status_{t['id']}")
            new_tech = st.selectbox("Assign Technician", list(tech_map.keys()),
                                    index=list(tech_map.keys()).index(t["technician"])
                                          if t["technician"] in tech_map else 0,
                                    key=f"tech_{t['id']}")

            if st.button("💾 Save Changes", key=f"save_{t['id']}", type="primary"):
                resolved_update = "resolved_at = NOW()," if new_status == "Resolved" else ""
                run_query(f"""
                    UPDATE tickets SET
                        status = %s,
                        assigned_tech_id = %s,
                        {resolved_update}
                        updated_at = NOW()
                    WHERE id = %s
                """, (new_status, tech_map[new_tech], t["id"]), fetch=False)
                st.success("✅ Updated!")
                st.rerun()

            if st.button("🗑️ Delete Ticket", key=f"del_{t['id']}"):
                st.session_state[f"confirm_del_{t['id']}"] = True

            if st.session_state.get(f"confirm_del_{t['id']}"):
                st.warning("⚠️ Are you sure? This cannot be undone.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("Yes, Delete", key=f"yes_del_{t['id']}", type="primary"):
                        run_query("DELETE FROM tickets WHERE id = %s", (t["id"],), fetch=False)
                        st.success("Deleted.")
                        st.rerun()
                with cc2:
                    if st.button("Cancel", key=f"no_del_{t['id']}"):
                        st.session_state[f"confirm_del_{t['id']}"] = False
                        st.rerun()
