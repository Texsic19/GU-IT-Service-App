import streamlit as st
from db import run_query, run_insert
from icons import icon_header, icon_text

st.markdown(icon_header("tag", "Manage Tags", level=1), unsafe_allow_html=True)
st.markdown('<p style="color:#6b7280;margin-top:0">Create and manage tags to label tickets.</p>', unsafe_allow_html=True)
st.divider()

with st.form("add_tag_form", clear_on_submit=True):
    c1, c2, c3 = st.columns([3,2,1])
    with c1:
        tag_name = st.text_input("Tag Name *", placeholder="e.g. wifi, printer, zoom")
    with c2:
        tag_color = st.color_picker("Color", value="#3B82F6")
    with c3:
        st.markdown("###")
        submitted = st.form_submit_button("Add Tag", type="primary", use_container_width=True)
    if submitted:
        if not tag_name.strip():
            st.error("Tag name is required.")
        elif len(tag_name.strip()) > 50:
            st.error("Tag name must be 50 characters or fewer.")
        else:
            try:
                run_insert("INSERT INTO tags (name, color) VALUES (%s,%s) RETURNING id", (tag_name.strip().lower(), tag_color))
                st.success(f"Tag '{tag_name}' added!")
                st.rerun()
            except Exception:
                st.error("Tag name already exists.")

tags = run_query("SELECT t.*, COUNT(tt.ticket_id) AS usage_count FROM tags t LEFT JOIN ticket_tags tt ON t.id=tt.tag_id GROUP BY t.id ORDER BY t.name")
st.markdown(f'<p style="font-size:0.9rem;color:#6b7280">{icon_text("tag", f"{len(tags)} tag(s)", 14, "#6b7280")}</p>', unsafe_allow_html=True)

cols = st.columns(3)
for i, tag in enumerate(tags):
    with cols[i % 3]:
        with st.container(border=True):
            tc1, tc2 = st.columns([3,1])
            with tc1:
                st.markdown(
                    f'<span style="background:{tag["color"]};color:white;padding:4px 14px;border-radius:20px;font-size:0.9rem;font-weight:500">#{tag["name"]}</span>'
                    f'<span style="color:#9ca3af;font-size:0.8rem;margin-left:8px">{tag["usage_count"]} ticket(s)</span>',
                    unsafe_allow_html=True)
            with tc2:
                if st.button("Delete", key=f"del_tag_{tag['id']}"):
                    st.session_state[f"confirm_del_tag_{tag['id']}"] = True
            if st.session_state.get(f"confirm_del_tag_{tag['id']}"):
                st.warning("Delete this tag?")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("Yes", key=f"yes_tag_{tag['id']}", type="primary"):
                        run_query("DELETE FROM tags WHERE id=%s", (tag["id"],), fetch=False)
                        st.rerun()
                with cc2:
                    if st.button("No", key=f"no_tag_{tag['id']}"):
                        st.session_state[f"confirm_del_tag_{tag['id']}"] = False
                        st.rerun()
