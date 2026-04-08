import streamlit as st
from db import run_query, run_insert
from ai_utils import ai_suggest_fix
from auth import require_staff, logout_button, role_badge

st.set_page_config(page_title="Ticket Detail", page_icon="🔍", layout="wide")

require_staff()
role_badge()
logout_button()


# ── Get ticket ID ─────────────────────────────────────────────
ticket_id = st.session_state.get("view_ticket_id")

if not ticket_id:
    ticket_id = st.number_input("Enter Ticket ID", min_value=1, step=1)
    if not ticket_id:
        st.info("Select a ticket from Manage Tickets or enter a ticket ID above.")
        st.stop()

ticket_id = int(ticket_id)

# ── Load ticket ───────────────────────────────────────────────
rows = run_query("""
    SELECT
        t.*,
        COALESCE(
            NULLIF(TRIM(u.first_name || ' ' || u.last_name), ''),
            NULLIF(TRIM(t.submitter_name), '')
        ) AS submitter_name,
        COALESCE(u.email, t.submitter_email) AS submitter_email,
        u.phone AS submitter_phone,
        u.department,
        COALESCE(tech.first_name || ' ' || tech.last_name, 'Unassigned') AS technician_name,
        tech.email AS tech_email
    FROM tickets t
    LEFT JOIN users u ON t.submitter_id = u.id
    LEFT JOIN technicians tech ON t.assigned_tech_id = tech.id
    WHERE t.id = %s
""", (ticket_id,))

if not rows:
    st.error(f"Ticket #{ticket_id} not found.")
    st.stop()

t = rows[0]

# ── Header ────────────────────────────────────────────────────
PRIORITY_COLORS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
STATUS_COLORS   = {"Open": "🔵", "In Progress": "🟣", "Resolved": "✅", "Closed": "⬛"}

st.title(f"🎫 Ticket #{t['id']}: {t['title']}")

badge_col1, badge_col2, badge_col3, badge_col4 = st.columns(4)
badge_col1.info(f"{STATUS_COLORS.get(t['status'], '⚪')} **{t['status']}**")
badge_col2.warning(f"{PRIORITY_COLORS.get(t['priority'], '⚪')} **{t['priority']}**")
badge_col3.success(f"📂 **{t['category']}**")
if t["ai_categorized"]:
    badge_col4.info("🤖 **AI Categorized**")

st.divider()

# ── Two-column layout ─────────────────────────────────────────
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("📄 Issue Description")
    st.markdown(t["description"])

    if t["location"]:
        st.markdown(f"📍 **Location:** {t['location']}")

    st.divider()
    st.subheader("👤 Submitter Information")
    sub_name = t.get("submitter_name") or "—"
    sub_email = t.get("submitter_email") or "—"
    st.markdown(
        f"**Name:** {sub_name}  \n"
        f"**Email:** {sub_email}  \n"
        f"**Phone:** {t.get('submitter_phone') or 'N/A'}  \n"
        f"**Department:** {t.get('department') or 'N/A'}"
    )

    st.divider()
    st.subheader("🔧 Assigned Technician")
    st.markdown(
        f"**Name:** {t['technician_name']}  \n"
        f"**Email:** {t.get('tech_email') or 'N/A'}"
    )

    st.divider()
    st.subheader("🏷️ Tags")
    ticket_tags = run_query("""
        SELECT tg.name, tg.color FROM ticket_tags tt
        JOIN tags tg ON tt.tag_id = tg.id
        WHERE tt.ticket_id = %s
    """, (ticket_id,))
    if ticket_tags:
        tag_html = " ".join([f'<span style="background:{tg["color"]};color:white;padding:3px 10px;border-radius:12px;font-size:0.85em">{tg["name"]}</span>' for tg in ticket_tags])
        st.markdown(tag_html, unsafe_allow_html=True)
    else:
        st.caption("No tags assigned.")

    # Add tags
    all_tags = run_query("SELECT id, name FROM tags ORDER BY name")
    existing_tag_names = [tg["name"] for tg in ticket_tags]
    available_tags = [tg for tg in all_tags if tg["name"] not in existing_tag_names]
    if available_tags:
        tag_map = {tg["name"]: tg["id"] for tg in available_tags}
        add_tag = st.selectbox("Add a tag", ["-- select --"] + list(tag_map.keys()), key="add_tag")
        if add_tag != "-- select --":
            run_query("INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                      (ticket_id, tag_map[add_tag]), fetch=False)
            st.rerun()

with right_col:
    # ── AI Suggested Fix ──────────────────────────────────────
    st.subheader("🤖 AI-Suggested Fix")
    st.caption("*Powered by Google Gemini*")

    existing_fix = (t.get("ai_suggested_fix") or "").strip()
    has_real_fix = bool(existing_fix) and not existing_fix.lower().startswith("ai suggestion unavailable")

    if has_real_fix:
        with st.container(border=True):
            st.markdown(existing_fix)

        if st.button("🔄 Regenerate AI Fix", use_container_width=True):
            with st.spinner("Generating new suggestion..."):
                new_fix = ai_suggest_fix(t["title"], t["description"], t["category"])
                run_query("UPDATE tickets SET ai_suggested_fix = %s WHERE id = %s",
                          (new_fix, ticket_id), fetch=False)
            st.rerun()
    else:
        st.info("No AI suggestion yet. Click Generate to create one.")
        if st.button("🤖 Generate AI Fix", use_container_width=True, type="primary"):
            with st.spinner("Generating suggestion..."):
                new_fix = ai_suggest_fix(t["title"], t["description"], t["category"])
                run_query("UPDATE tickets SET ai_suggested_fix = %s, ai_categorized = TRUE WHERE id = %s",
                          (new_fix, ticket_id), fetch=False)
            st.rerun()

    st.divider()

    # ── Quick Update ──────────────────────────────────────────
    st.subheader("⚡ Quick Update")
    techs = run_query("SELECT id, first_name || ' ' || last_name AS name FROM technicians WHERE is_active = TRUE ORDER BY last_name")
    tech_options = {"Unassigned": None}
    tech_options.update({tc["name"]: tc["id"] for tc in techs})

    with st.form("quick_update"):
        new_status = st.selectbox("Status",
            ["Open", "In Progress", "Resolved", "Closed"],
            index=["Open", "In Progress", "Resolved", "Closed"].index(t["status"]))
        new_tech = st.selectbox("Assigned To", list(tech_options.keys()),
            index=list(tech_options.keys()).index(t["technician_name"])
                  if t["technician_name"] in tech_options else 0)
        if st.form_submit_button("💾 Update", use_container_width=True, type="primary"):
            resolved_clause = "resolved_at = NOW()," if new_status == "Resolved" else ""
            run_query(f"""
                UPDATE tickets SET status = %s, assigned_tech_id = %s,
                {resolved_clause} updated_at = NOW() WHERE id = %s
            """, (new_status, tech_options[new_tech], ticket_id), fetch=False)
            st.success("Updated!")
            st.rerun()

    st.divider()
    st.caption(f"📅 Created: {str(t['created_at'])[:16]}")
    st.caption(f"🔄 Updated: {str(t['updated_at'])[:16]}")
    if t["resolved_at"]:
        st.caption(f"✅ Resolved: {str(t['resolved_at'])[:16]}")
