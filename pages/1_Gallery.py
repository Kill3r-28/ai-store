import streamlit as st

from lib.auth import render_sidebar_status
from lib.config import STARTER_USE_CASE_TAGS, TOOL_TYPES
from lib.db import get_all_tags, init_db, list_tools
from lib.theme import apply_app_theme
from lib.routes import REGISTER_SCRIPT
from lib.ui import render_tool_card


def _gallery_tag_order(tools: list) -> list[str]:
    used: set[str] = set()
    for t in tools:
        used.update(t.use_case_tags)
    ordered = [tag for tag in STARTER_USE_CASE_TAGS if tag in used]
    for tag in sorted(used):
        if tag not in ordered:
            ordered.append(tag)
    return ordered


apply_app_theme()
init_db()
render_sidebar_status()

st.title("NxtWave AI Tools Marketplace")
st.caption("Tools are grouped by hashtag. Pick a tag in the sidebar to focus on one group.")

all_known_tags = get_all_tags()
sidebar_tags = ["all"] + sorted(set(STARTER_USE_CASE_TAGS) | set(all_known_tags))

with st.sidebar:
    st.header("Filters")
    search = st.text_input("Search", placeholder="Name or description")
    tool_type = st.selectbox(
        "Type",
        ["all", *TOOL_TYPES],
        format_func=lambda x: x.replace("_", " ").title() if x != "all" else "All types",
    )
    tag = st.selectbox(
        "Hashtag",
        sidebar_tags,
        format_func=lambda x: "All hashtags" if x == "all" else f"#{x}",
    )

tools = list_tools(
    search=search or None,
    tool_type=tool_type if tool_type != "all" else None,
    tag=tag if tag != "all" else None,
)

if not tools:
    st.info("No tools match your filters. Be the first to register one!")
    if st.button("Register a tool", type="primary"):
        st.switch_page(REGISTER_SCRIPT)
    st.stop()

tags_to_show = [tag] if tag != "all" else _gallery_tag_order(tools)
shown_ids: set[str] = set()

for hashtag in tags_to_show:
    tag_tools = [t for t in tools if hashtag in t.use_case_tags]
    if not tag_tools:
        continue
    st.subheader(f"#{hashtag}")
    st.caption(f"{len(tag_tools)} tool(s)")
    cols = st.columns(3)
    for i, t in enumerate(tag_tools):
        shown_ids.add(t.id)
        with cols[i % 3]:
            with st.container(border=True):
                render_tool_card(t, key_prefix=f"{hashtag}_{i}")
    st.divider()

other = [t for t in tools if t.id not in shown_ids]
if other:
    st.subheader("Other tools")
    cols = st.columns(3)
    for i, t in enumerate(other):
        with cols[i % 3]:
            with st.container(border=True):
                render_tool_card(t, key_prefix=f"other_{i}")
