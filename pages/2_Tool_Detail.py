import streamlit as st

from lib.auth import is_admin, render_sidebar_status
from lib.config import INFRA_CHECKLIST_KEYS, INFRA_RECOMMENDATIONS
from lib.db import delete_tool, get_tool, init_db
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
render_sidebar_status()

tool_id = st.query_params.get("tool")
if not tool_id:
    st.warning("No tool selected. Pick one from the Gallery.")
    if st.button("Back to Gallery"):
        st.switch_page(GALLERY_SCRIPT)
    st.stop()

tool = get_tool(tool_id)
if not tool:
    st.error("Tool not found.")
    if st.button("Back to Gallery", key="back_not_found"):
        st.switch_page(GALLERY_SCRIPT)
    st.stop()

st.title(tool.name)
col_meta1, col_meta2 = st.columns(2)
with col_meta1:
    submitter = tool.submitter_name or "—"
    if tool.submitter_email:
        submitter = f"{submitter} ({tool.submitter_email})"
    st.markdown(f"{bold('Submitted by:')} {submitter}", unsafe_allow_html=True)
with col_meta2:
    st.markdown(
        f"{bold('Type:')} {TYPE_LABELS.get(tool.tool_type, tool.tool_type)}",
        unsafe_allow_html=True,
    )

if tool.use_case_tags:
    st.caption("Hashtags: " + " · ".join(f"`#{t}`" for t in tool.use_case_tags))

if tool.github_repo and st.button("Refresh docs from GitHub"):
    refresh_tool_docs(tool)
    st.success("Docs refreshed.")
    st.rerun()

tab_overview, tab_readme, tab_roadmap, tab_infra = st.tabs(
    ["Overview", "README", "Roadmap", "Infra score"]
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

with tab_infra:
    score, max_score, merged = infra_score_summary(tool)
    st.metric("Infrastructure score", f"{score}/{max_score}")
    docs_ok = bool(tool.readme_fallback) and bool(tool.future_plans_fallback)
    st.write(f"{'✅' if docs_ok else '⬜'} README.md and future_plans.md provided at registration")
    labels = {
        "has_ci_cd": "CI/CD integrated",
        "has_tests": "Automated tests",
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

st.divider()
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Edit this tool"):
        st.query_params["edit"] = tool.id
        st.switch_page(REGISTER_SCRIPT)
with col_b:
    if st.button("← Back to Gallery", key="back_footer"):
        st.switch_page(GALLERY_SCRIPT)

if is_admin():
    st.divider()
    st.markdown(f"{bold('Admin')}", unsafe_allow_html=True)
    confirm_key = f"confirm_delete_{tool.id}"
    if st.session_state.get(confirm_key):
        st.warning(f"Delete **{tool.name}** permanently? This cannot be undone.")
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
