import streamlit as st
from db import run_query
from ai_utils import ai_suggest_fix
from auth import require_staff, logout_button, role_badge
from icons import icon, icon_text, icon_header
from nav import apply_nav_visibility

st.set_page_config(page_title="Ticket Detail", page_icon="🔍", layout="wide")
require_staff()
role_badge()
logout_button()
apply_nav_visibility()

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
    SELECT t.*,
        COALESCE(NULLIF(TRIM(t.submitter_name), ''), 'Unknown') AS display_submitter_name,
        COALESCE(t.submitter_email, '—') AS display_submitter_email,
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
# Solid color badges — work in both light and dark mode
PRIORITY_BADGE = {
    "Critical": ("alert-triangle", "#ffffff", "#dc2626"),
    "High":     ("zap",            "#ffffff", "#d97706"),
    "Medium":   ("info",           "#ffffff", "#2563eb"),
    "Low":      ("check-circle",   "#ffffff", "#16a34a"),
}
STATUS_BADGE = {
    "Open":        ("circle-dot",   "#ffffff", "#ca8a04"),
    "In Progress": ("clock",        "#ffffff", "#7c3aed"),
    "Resolved":    ("check-circle", "#ffffff", "#16a34a"),
    "Closed":      ("x-circle",     "#ffffff", "#6b7280"),
}

p_ico, p_txt, p_bg = PRIORITY_BADGE.get(t["priority"], ("circle-dot", "#ffffff", "#6b7280"))
s_ico, s_txt, s_bg = STATUS_BADGE.get(t["status"],     ("circle-dot", "#ffffff", "#6b7280"))

title_str = f"Ticket #{t['id']}: {t['title']}"
st.markdown(icon_header("ticket", title_str, level=1), unsafe_allow_html=True)

cat_icon = {"Network":"wifi","Hardware":"cpu","Software":"monitor","Account/Access":"key",
            "AV Equipment":"tv","Email":"mail","Printing":"printer"}.get(t["category"],"wrench")

b1, b2, b3, b4 = st.columns(4)
with b1:
    st.markdown(
        f'<div style="background:{s_bg};border-radius:8px;padding:10px 14px;'
        f'font-size:0.9rem;color:white;font-weight:500">'
        f'{icon_text(s_ico, t["status"], 15, "white")}</div>', unsafe_allow_html=True)
with b2:
    st.markdown(
        f'<div style="background:{p_bg};border-radius:8px;padding:10px 14px;'
        f'font-size:0.9rem;color:white;font-weight:500">'
        f'{icon_text(p_ico, t["priority"], 15, "white")}</div>', unsafe_allow_html=True)
with b3:
    st.markdown(
        f'<div style="background:#166534;border-radius:8px;padding:10px 14px;'
        f'font-size:0.9rem;color:white;font-weight:500">'
        f'{icon_text(cat_icon, t["category"], 15, "white")}</div>', unsafe_allow_html=True)
with b4:
    if t["ai_categorized"]:
        st.markdown(
            f'<div style="background:#7c3aed;border-radius:8px;padding:10px 14px;'
            f'font-size:0.9rem;color:white;font-weight:500">'
            f'{icon_text("sparkles", "AI Categorized", 15, "white")}</div>', unsafe_allow_html=True)

st.divider()

left_col, right_col = st.columns([3, 2])

with left_col:
    st.markdown(icon_header("eye", "Issue Description", level=3), unsafe_allow_html=True)
    st.markdown(t["description"])
    if t.get("location"):
        st.markdown(
            f'<p style="font-size:0.9rem">{icon_text("map-pin", t["location"], 14, "#6b7280")}</p>',
            unsafe_allow_html=True)

    st.divider()
    st.markdown(icon_header("user", "Submitter", level=3), unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.9rem;display:grid;gap:6px">'
        f'<div>{icon_text("user", t["display_submitter_name"], 14)}</div>'
        f'<div>{icon_text("mail", t["display_submitter_email"], 14)}</div>'
        f'<div>{icon_text("wrench", t.get("department") or "N/A", 14)}</div>'
        f'</div>',
        unsafe_allow_html=True)

    st.divider()
    st.markdown(icon_header("wrench", "Assigned Technician", level=3), unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.9rem;display:grid;gap:6px">'
        f'<div>{icon_text("user", t["technician_name"], 14)}</div>'
        f'<div>{icon_text("mail", t.get("tech_email") or "N/A", 14)}</div>'
        f'</div>',
        unsafe_allow_html=True)

    st.divider()
    st.markdown(icon_header("tag", "Tags", level=3), unsafe_allow_html=True)
    ticket_tags = run_query("""
        SELECT tg.name, tg.color FROM ticket_tags tt
        JOIN tags tg ON tt.tag_id = tg.id WHERE tt.ticket_id = %s
    """, (ticket_id,))
    if ticket_tags:
        tag_html = " ".join([
            f'<span style="background:{tg["color"]};color:white;padding:3px 12px;'
            f'border-radius:20px;font-size:0.82rem;font-weight:500">#{tg["name"]}</span>'
            for tg in ticket_tags
        ])
        st.markdown(tag_html, unsafe_allow_html=True)
    else:
        st.caption("No tags assigned.")

    all_tags = run_query("SELECT id, name FROM tags ORDER BY name")
    existing_names = [tg["name"] for tg in ticket_tags]
    available = [tg for tg in all_tags if tg["name"] not in existing_names]
    if available:
        tag_map = {tg["name"]: tg["id"] for tg in available}
        add_tag = st.selectbox("Add a tag", ["— select —"] + list(tag_map.keys()), key="add_tag")
        if add_tag != "— select —":
            run_query("INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                      (ticket_id, tag_map[add_tag]), fetch=False)
            st.rerun()

with right_col:
    st.markdown(icon_header("bot", "AI-Suggested Fix", level=3), unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:0.82rem;color:#6b7280;margin-top:-8px">'
        f'{icon_text("sparkles", "Powered by Google Gemini", 12, "#9ca3af")}'
        f'</p>',
        unsafe_allow_html=True)

    existing_fix = (t.get("ai_suggested_fix") or "").strip()
    has_fix = bool(existing_fix) and not existing_fix.lower().startswith("ai suggestion unavailable")

    if has_fix:
        with st.container(border=True):
            st.markdown(existing_fix)
        if st.button("Regenerate AI Fix", use_container_width=True):
            with st.spinner("Generating new suggestion..."):
                new_fix = ai_suggest_fix(t["title"], t["description"], t["category"])
                run_query("UPDATE tickets SET ai_suggested_fix=%s WHERE id=%s",
                          (new_fix, ticket_id), fetch=False)
            st.rerun()
    else:
        st.info("No AI suggestion yet.")
        if st.button("Generate AI Fix", use_container_width=True, type="primary"):
            with st.spinner("Generating suggestion..."):
                new_fix = ai_suggest_fix(t["title"], t["description"], t["category"])
                run_query("UPDATE tickets SET ai_suggested_fix=%s, ai_categorized=TRUE WHERE id=%s",
                          (new_fix, ticket_id), fetch=False)
            st.rerun()

    st.divider()
    st.markdown(icon_header("zap", "Quick Update", level=3), unsafe_allow_html=True)
    techs = run_query("SELECT id, first_name || ' ' || last_name AS name FROM technicians WHERE is_active=TRUE ORDER BY last_name")
    tech_options = {"Unassigned": None}
    tech_options.update({tc["name"]: tc["id"] for tc in techs})

    with st.form("quick_update"):
        new_status = st.selectbox("Status", ["Open","In Progress","Resolved","Closed"],
            index=["Open","In Progress","Resolved","Closed"].index(t["status"]))
        new_tech = st.selectbox("Assigned To", list(tech_options.keys()),
            index=list(tech_options.keys()).index(t["technician_name"])
                  if t["technician_name"] in tech_options else 0)
        if st.form_submit_button("Save Update", use_container_width=True, type="primary"):
            resolved_clause = "resolved_at=NOW()," if new_status == "Resolved" else ""
            run_query(f"UPDATE tickets SET status=%s,assigned_tech_id=%s,{resolved_clause}updated_at=NOW() WHERE id=%s",
                      (new_status, tech_options[new_tech], ticket_id), fetch=False)
            st.success("Updated!")
            st.rerun()

    st.divider()
    created_str  = str(t["created_at"])[:16]
    updated_str  = str(t["updated_at"])[:16]
    resolved_str = str(t["resolved_at"])[:16] if t["resolved_at"] else None
    resolved_html = (
        f'<div>{icon_text("check-circle", f"Resolved: {resolved_str}", 12, "#16a34a")}</div>'
        if resolved_str else ""
    )
    st.markdown(
        f'<div style="font-size:0.8rem;color:#9ca3af;display:grid;gap:4px">'
        f'<div>{icon_text("clock", f"Created: {created_str}", 12, "#9ca3af")}</div>'
        f'<div>{icon_text("refresh-cw", f"Updated: {updated_str}", 12, "#9ca3af")}</div>'
        f'{resolved_html}'
        f'</div>',
        unsafe_allow_html=True)
