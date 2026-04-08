import streamlit as st
from auth import require_staff, logout_button, role_badge
from db import run_query
from icons import icon, icon_text, icon_header
import pandas as pd
from nav import apply_nav_visibility

st.set_page_config(
    page_title="GU IT Help Desk — Dashboard",
    page_icon="🔧",
    layout="wide"
)

require_staff()
role_badge()
logout_button()
apply_nav_visibility()

# ── Header ────────────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:0.25rem">'
    f'<div style="background:#002147;border-radius:10px;padding:10px;display:inline-flex">'
    f'{icon("wrench", 28, "white")}'
    f'</div>'
    f'<div>'
    f'<h1 style="margin:0;font-size:1.75rem;font-weight:700;color:#002147">Gonzaga University IT Help Desk</h1>'
    f'<p style="margin:0;color:#6b7280;font-size:0.9rem">Information Technology Services — Internal Dashboard</p>'
    f'</div></div>',
    unsafe_allow_html=True
)
st.divider()

# ── Metrics ───────────────────────────────────────────────────
metrics = run_query("""
    SELECT
        COUNT(*) FILTER (WHERE status = 'Open')          AS open_tickets,
        COUNT(*) FILTER (WHERE status = 'In Progress')   AS in_progress,
        COUNT(*) FILTER (WHERE status = 'Resolved'
            AND resolved_at >= NOW() - INTERVAL '7 days') AS resolved_week,
        COUNT(*) FILTER (WHERE priority = 'Critical'
            AND status NOT IN ('Resolved','Closed'))      AS critical_open
    FROM tickets
""")
m = metrics[0] if metrics else {}

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f'<div style="background:#fefce8;border:1px solid #fde047;border-radius:12px;padding:1.25rem">'
        f'{icon_text("ticket", "Open Tickets", 16, "#854d0e")}'
        f'<div style="font-size:2rem;font-weight:700;color:#854d0e;margin-top:6px">{m.get("open_tickets", 0)}</div>'
        f'</div>', unsafe_allow_html=True)

with c2:
    st.markdown(
        f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:1.25rem">'
        f'{icon_text("clock", "In Progress", 16, "#1d4ed8")}'
        f'<div style="font-size:2rem;font-weight:700;color:#1d4ed8;margin-top:6px">{m.get("in_progress", 0)}</div>'
        f'</div>', unsafe_allow_html=True)

with c3:
    st.markdown(
        f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:1.25rem">'
        f'{icon_text("check-circle", "Resolved (7d)", 16, "#15803d")}'
        f'<div style="font-size:2rem;font-weight:700;color:#15803d;margin-top:6px">{m.get("resolved_week", 0)}</div>'
        f'</div>', unsafe_allow_html=True)

with c4:
    st.markdown(
        f'<div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:12px;padding:1.25rem">'
        f'{icon_text("alert-triangle", "Critical Open", 16, "#b91c1c")}'
        f'<div style="font-size:2rem;font-weight:700;color:#b91c1c;margin-top:6px">{m.get("critical_open", 0)}</div>'
        f'</div>', unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.markdown(icon_header("bar-chart-2", "Tickets by Category"), unsafe_allow_html=True)
    cat_data = run_query("""
        SELECT category, COUNT(*) AS count
        FROM tickets GROUP BY category ORDER BY count DESC
    """)
    if cat_data:
        st.bar_chart(pd.DataFrame(cat_data).set_index("category"))
    else:
        st.info("No ticket data yet.")

with right:
    st.markdown(icon_header("zap", "Tickets by Priority"), unsafe_allow_html=True)
    pri_data = run_query("""
        SELECT priority, COUNT(*) AS count FROM tickets
        GROUP BY priority
        ORDER BY CASE priority
            WHEN 'Critical' THEN 1 WHEN 'High' THEN 2
            WHEN 'Medium' THEN 3 ELSE 4 END
    """)
    if pri_data:
        st.bar_chart(pd.DataFrame(pri_data).set_index("priority"))
    else:
        st.info("No ticket data yet.")

st.divider()

# ── Recent Tickets ────────────────────────────────────────────
st.markdown(icon_header("list-filter", "Recent Tickets"), unsafe_allow_html=True)

recent = run_query("""
    SELECT
        t.id,
        t.title,
        t.category,
        t.priority,
        t.status,
        COALESCE(t.submitter_name, 'Unknown') AS submitter,
        COALESCE(tech.first_name || ' ' || tech.last_name, 'Unassigned') AS technician,
        t.created_at::date AS submitted
    FROM tickets t
    LEFT JOIN technicians tech ON t.assigned_tech_id = tech.id
    ORDER BY t.created_at DESC LIMIT 15
""")

if recent:
    df = pd.DataFrame(recent)
    def color_priority(val):
        colors = {
            "Critical": "background-color:#fee2e2;color:#991b1b",
            "High":     "background-color:#fef3c7;color:#92400e",
            "Medium":   "background-color:#dbeafe;color:#1e40af",
            "Low":      "background-color:#dcfce7;color:#166534"
        }
        return colors.get(val, "")
    st.dataframe(
        df.style.map(color_priority, subset=["priority"]),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No tickets submitted yet.")

st.markdown(
    f'<div style="text-align:right;color:#9ca3af;font-size:0.8rem;margin-top:1rem">'
    f'{icon_text("shield", "Gonzaga University Information Technology Services", 13, "#9ca3af")}'
    f'</div>',
    unsafe_allow_html=True
)
