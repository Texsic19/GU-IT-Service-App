import streamlit as st
from auth import login_page, logout_button, role_badge
from db import run_query
import pandas as pd

# ── Auth gate ─────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    login_page()
    st.stop()

if st.session_state.get("role") == "student":
    st.switch_page("pages/1_Submit_Ticket.py")

st.set_page_config(
    page_title="GU IT Help Desk",
    page_icon="🔧",
    layout="wide"
)

role_badge()
logout_button()

# ── Header ──────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## 🦾")
with col_title:
    st.markdown("# Gonzaga University IT Help Desk")
    st.markdown("*Information Technology Services — Internal Ticketing System*")

st.divider()

# ── Summary Metrics ─────────────────────────────────────────
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
c1.metric("🟡 Open Tickets",     m.get("open_tickets", 0))
c2.metric("🔵 In Progress",      m.get("in_progress", 0))
c3.metric("✅ Resolved (7 days)", m.get("resolved_week", 0))
c4.metric("🔴 Critical / Open",  m.get("critical_open", 0),
          delta_color="inverse")

st.divider()

# ── Charts Row ───────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Tickets by Category")
    cat_data = run_query("""
        SELECT category, COUNT(*) AS count
        FROM tickets
        GROUP BY category ORDER BY count DESC
    """)
    if cat_data:
        df_cat = pd.DataFrame(cat_data).set_index("category")
        st.bar_chart(df_cat)
    else:
        st.info("No ticket data yet.")

with right:
    st.subheader("Tickets by Priority")
    pri_data = run_query("""
        SELECT priority, COUNT(*) AS count
        FROM tickets
        GROUP BY priority
        ORDER BY CASE priority
            WHEN 'Critical' THEN 1 WHEN 'High' THEN 2
            WHEN 'Medium' THEN 3 ELSE 4 END
    """)
    if pri_data:
        df_pri = pd.DataFrame(pri_data).set_index("priority")
        st.bar_chart(df_pri)
    else:
        st.info("No ticket data yet.")

st.divider()

# ── Recent Tickets Table ─────────────────────────────────────
st.subheader("📋 Recent Tickets")

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
    ORDER BY t.created_at DESC
    LIMIT 15
""")

if recent:
    df = pd.DataFrame(recent)

    def color_priority(val):
        colors = {"Critical": "background-color:#fee2e2",
                  "High": "background-color:#fef3c7",
                  "Medium": "background-color:#dbeafe",
                  "Low": "background-color:#dcfce7"}
        return colors.get(val, "")

    st.dataframe(
        df.style.map(color_priority, subset=["priority"]),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No tickets submitted yet. Use **Submit a Ticket** to get started.")

st.caption("Gonzaga University Information Technology Services · Built with Streamlit + Supabase")
