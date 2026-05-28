from __future__ import annotations

import streamlit as st

from lib.formatting import bold
from lib.models import Tool
from lib.routes import DETAIL_SCRIPT


TYPE_LABELS = {
    "streamlit": "Streamlit",
    "github_only": "GitHub",
    "apps_script": "Apps Script",
}


def tool_launch_url(tool: Tool) -> str | None:
    if tool.tool_type == "streamlit":
        return tool.app_url
    if tool.tool_type == "github_only" and tool.github_repo:
        repo = tool.github_repo.strip()
        if repo.startswith("http"):
            return repo
        return f"https://github.com/{repo}"
    if tool.tool_type == "apps_script":
        return tool.sheet_url
    return tool.app_url or tool.sheet_url


def render_tool_card(tool: Tool, *, key_prefix: str = "") -> None:
    type_label = TYPE_LABELS.get(tool.tool_type, tool.tool_type)

    st.markdown(bold(tool.name), unsafe_allow_html=True)
    submitter = tool.submitter_name or "—"
    st.caption(f"{type_label} · {submitter}")
    st.write(tool.short_desc[:120] + ("…" if len(tool.short_desc) > 120 else ""))
    if tool.use_case_tags:
        st.caption(" ".join(f"`#{t}`" for t in tool.use_case_tags[:4]))

    if st.button("Details", key=f"detail_{key_prefix}_{tool.id}", use_container_width=True):
        st.query_params["tool"] = tool.id
        st.switch_page(DETAIL_SCRIPT)
