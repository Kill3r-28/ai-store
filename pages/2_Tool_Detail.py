import streamlit as st

from lib.auth import require_login, render_user_sidebar
from lib.config import COMMENT_STATUSES, INFRA_CHECKLIST_KEYS, INFRA_RECOMMENDATIONS, is_admin
from lib.db import (
    add_comment,
    delete_tool,
    get_tool,
    get_user_rating,
    init_db,
    list_comments,
    set_rating,
    toggle_like,
    update_comment_status,
)
from lib.github_docs import (
    get_tool_future_plans,
    get_tool_readme,
    infra_score_summary,
    refresh_tool_docs,
)
from lib.formatting import bold
from lib.theme import apply_app_theme
from lib.routes import GALLERY_SCRIPT, REGISTER_SCRIPT
from lib.ui import TYPE_LABELS, tool_launch_url

apply_app_theme()
init_db()
user_email, user_name = require_login()
render_user_sidebar()

tool_id = st.query_params.get("tool")
if not tool_id:
    st.warning("No tool selected. Pick one from the Gallery.")
    if st.button("Back to Gallery"):
        st.switch_page(GALLERY_SCRIPT)
    st.stop()

tool = get_tool(tool_id, user_email)
if not tool:
    st.error("Tool not found.")
    if st.button("Back to Gallery", key="back_not_found"):
        st.switch_page(GALLERY_SCRIPT)
    st.stop()

is_owner = tool.owner_email.lower() == user_email.lower()
user_is_admin = is_admin(user_email)

st.title(tool.name)
col_meta1, col_meta2 = st.columns(2)
with col_meta1:
    st.markdown(f"{bold('Owner:')} {tool.owner_name} ({tool.owner_email})", unsafe_allow_html=True)
with col_meta2:
    st.markdown(
        f"{bold('Type:')} {TYPE_LABELS.get(tool.tool_type, tool.tool_type)}",
        unsafe_allow_html=True,
    )

if tool.use_case_tags:
    st.caption("Hashtags: " + " · ".join(f"`#{t}`" for t in tool.use_case_tags))

like_col, rating_col = st.columns([1, 2])
with like_col:
    liked_label = "❤️ Liked" if tool.user_liked else "🤍 Like"
    if st.button(liked_label, key="toggle_like"):
        toggle_like(tool.id, user_email)
        st.rerun()
    st.caption(f"{tool.like_count} likes")
with rating_col:
    current_rating = get_user_rating(tool.id, user_email)
    score = st.select_slider(
        "Your rating (1–5)",
        options=[1, 2, 3, 4, 5],
        value=current_rating or 3,
        key="user_rating",
    )
    if st.button("Submit rating", key="submit_rating"):
        set_rating(tool.id, user_email, score)
        st.success("Rating saved!")
        st.rerun()

if is_owner and tool.github_repo:
    if st.button("Refresh docs from GitHub"):
        refresh_tool_docs(tool)
        st.success("Docs refreshed.")
        st.rerun()

if user_is_admin:
    st.divider()
    st.markdown(f"{bold('Admin')}", unsafe_allow_html=True)
    confirm_key = f"confirm_delete_{tool.id}"
    if st.session_state.get(confirm_key):
        st.warning(f"Delete {tool.name} permanently? This cannot be undone.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete tool", type="primary", key=f"yes_del_{tool.id}"):
                delete_tool(tool.id)
                st.session_state.pop(confirm_key, None)
                st.success("Tool deleted.")
                st.switch_page(GALLERY_SCRIPT)
        with c2:
            if st.button("Cancel", key=f"no_del_{tool.id}"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
    elif st.button("Delete tool", key=f"del_{tool.id}"):
        st.session_state[confirm_key] = True
        st.rerun()

tab_overview, tab_readme, tab_roadmap, tab_feedback, tab_infra = st.tabs(
    ["Overview", "README", "Roadmap", "Feedback", "Infra score"]
)

with tab_overview:
    st.markdown(tool.short_desc)
    launch_url = tool_launch_url(tool)
    if launch_url:
        st.link_button("Open tool", launch_url)
    if tool.github_repo:
        repo_url = (
            tool.github_repo
            if tool.github_repo.startswith("http")
            else f"https://github.com/{tool.github_repo}"
        )
        st.link_button("GitHub repository", repo_url)
    if tool.app_url and tool.tool_type == "streamlit":
        st.link_button("Streamlit app", tool.app_url)
    if tool.sheet_url:
        st.link_button("Google Sheet", tool.sheet_url)

with tab_readme:
    st.markdown(get_tool_readme(tool))

with tab_roadmap:
    st.markdown(get_tool_future_plans(tool))

with tab_feedback:
    st.subheader("Comments")
    comments = list_comments(tool.id)
    if not comments:
        st.caption("No comments yet.")
    for c in comments:
        with st.container(border=True):
            st.markdown(
                f"{bold(c.user_name)} · `{c.status}` · {c.created_at[:10]}",
                unsafe_allow_html=True,
            )
            st.write(c.body)
            if is_owner:
                new_status = st.selectbox(
                    "Status",
                    COMMENT_STATUSES,
                    index=COMMENT_STATUSES.index(c.status) if c.status in COMMENT_STATUSES else 0,
                    key=f"status_{c.id}",
                )
                if new_status != c.status:
                    if st.button("Update status", key=f"upd_{c.id}"):
                        update_comment_status(c.id, new_status)
                        st.rerun()

    st.divider()
    with st.form("add_comment"):
        body = st.text_area("Add a comment or feature request")
        if st.form_submit_button("Post comment"):
            if body.strip():
                add_comment(tool.id, user_email, user_name, body.strip())
                st.success("Comment posted.")
                st.rerun()
            else:
                st.warning("Comment cannot be empty.")

with tab_infra:
    score, max_score, merged = infra_score_summary(tool)
    st.metric("Infrastructure score", f"{score}/{max_score}")
    docs_ok = bool(tool.readme_fallback) and bool(tool.future_plans_fallback)
    st.write(f"{'✅' if docs_ok else '⬜'} README.md and future_plans.md provided at registration")
    labels = {
        "has_ci_cd": "CI/CD integrated",
        "has_tests": "Automated tests",
        "has_tool_auth": "Secure login on the tool",
    }
    for key in INFRA_CHECKLIST_KEYS:
        ok = merged.get(key, False)
        st.write(f"{'✅' if ok else '⬜'} {labels.get(key, key)}")
        if not ok:
            st.caption(INFRA_RECOMMENDATIONS.get(key, ""))
    gh_keys = [k for k in merged if k.startswith("gh_")]
    if gh_keys:
        st.caption("GitHub auto-detected")
        for k in gh_keys:
            label = k.replace("gh_", "").replace("_", " ").title()
            st.write(f"{'✅' if merged[k] else '⬜'} {label} (GitHub)")

if is_owner:
    st.divider()
    if st.button("Edit this tool"):
        st.query_params["edit"] = tool.id
        st.switch_page(REGISTER_SCRIPT)

if st.button("← Back to Gallery", key="back_footer"):
    st.switch_page(GALLERY_SCRIPT)
