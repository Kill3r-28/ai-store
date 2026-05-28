import streamlit as st

from lib.auth import current_user, render_sidebar_status
from lib.config import (
    INFRA_CHECKLIST_KEYS,
    INFRA_RECOMMENDATIONS,
    STARTER_USE_CASE_TAGS,
    TOOL_TYPES,
)
from lib.db import create_tool, get_tool, init_db, normalize_tag, update_tool
from lib.formatting import bold, bold_line, rich
from lib.models import Tool
from lib.routes import DETAIL_SCRIPT, LOGIN_SCRIPT
from lib.theme import apply_app_theme

apply_app_theme()
init_db()
render_sidebar_status()

if current_user() is None:
    st.title("Sign in to register a tool")
    st.write("Adding a tool requires a NxtWave Google account or the admin login.")
    if st.button("Go to sign-in", type="primary"):
        st.switch_page(LOGIN_SCRIPT)
    st.stop()

edit_id = st.query_params.get("edit")
existing: Tool | None = get_tool(edit_id) if edit_id else None

st.title("Edit tool" if existing else "Register a new tool")

default_type = existing.tool_type if existing else "streamlit"
type_index = TOOL_TYPES.index(default_type) if default_type in TOOL_TYPES else 0
tool_type = st.selectbox(
    "Tool type *",
    TOOL_TYPES,
    index=type_index,
    format_func=lambda x: x.replace("_", " ").title(),
    key="register_tool_type",
)

if tool_type == "apps_script":
    rich(
        "Recommendation: Apps Script tools are easier to version, review, and maintain "
        f"when the logic also lives in a {bold('GitHub repo')}. Consider linking a repo below "
        "even if the UI stays in Google Sheets."
    )

# --- Hashtags (outside form so Add / toggles work) ---
tags_key = f"register_tags_{edit_id or 'new'}"
if tags_key not in st.session_state:
    st.session_state[tags_key] = list(existing.use_case_tags) if existing else []

bold_line("Use case hashtags", required=True)
st.caption("Grouped in the Gallery by tag.")

selected_tags: list[str] = st.session_state[tags_key]
if selected_tags:
    chips = " ".join(
        f"<span style='display:inline-block;padding:0.15rem 0.55rem;margin:0 0.25rem 0.25rem 0;"
        f"border:1px solid #333;border-radius:999px;font-size:0.8rem;'>#{t}</span>"
        for t in selected_tags
    )
    st.markdown(chips, unsafe_allow_html=True)

tag_panel, _sp = st.columns([1, 2])
with tag_panel:
    st.markdown('<div class="hashtag-compact-wrap">', unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("Starter tags")
        n = len(STARTER_USE_CASE_TAGS)
        starter_cols = st.columns([1] * n)
        for i, tag in enumerate(STARTER_USE_CASE_TAGS):
            with starter_cols[i]:
                is_on = tag in selected_tags
                btn_label = f"#{tag} ✓" if is_on else f"#{tag}"
                if st.button(btn_label, key=f"toggle_starter_{tag}_{tags_key}"):
                    if is_on:
                        selected_tags.remove(tag)
                    else:
                        selected_tags.append(tag)
                    st.session_state[tags_key] = selected_tags
                    st.rerun()
        st.caption("Add more")
        add_in, add_btn = st.columns([3, 1])
        with add_in:
            new_tags_raw = st.text_input(
                "Add hashtags",
                placeholder="finance, analytics",
                key=f"new_tags_input_{tags_key}",
                label_visibility="collapsed",
            )
        with add_btn:
            st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
            if st.button("Add", key=f"add_tags_{tags_key}"):
                added = []
                for part in new_tags_raw.split(","):
                    t = normalize_tag(part)
                    if t and t not in st.session_state[tags_key]:
                        st.session_state[tags_key].append(t)
                        added.append(t)
                if added:
                    st.rerun()
                elif new_tags_raw.strip():
                    st.warning("Use letters, numbers, and hyphens only.")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

with st.form("register_tool", clear_on_submit=not existing):
    name = st.text_input("Tool name *", value=existing.name if existing else "")
    short_desc = st.text_area(
        "Short description (gallery card) *",
        value=existing.short_desc if existing else "",
    )

    bold_line("Submitter")
    _u = current_user()
    _default_name = ""
    _default_email = ""
    if existing:
        _default_name = existing.submitter_name
        _default_email = existing.submitter_email
    elif _u and _u.role == "google":
        _default_name = _u.name
        _default_email = _u.email
    submitter_name = st.text_input("Your name *", value=_default_name)
    submitter_email = st.text_input("Your email (optional)", value=_default_email)

    app_url = ""
    github_repo = ""
    sheet_url = ""

    if tool_type == "streamlit":
        bold_line("Streamlit hosting")
        app_url = st.text_input(
            "Streamlit app URL *",
            value=existing.app_url or "" if existing else "",
            placeholder="https://your-app.streamlit.app",
        )
        github_repo = st.text_input(
            "GitHub repo * (org/repo or full URL)",
            value=existing.github_repo or "" if existing else "",
            placeholder="nxtwave/my-tool",
        )
    elif tool_type == "github_only":
        bold_line("GitHub repository")
        github_repo = st.text_input(
            "GitHub repo * (org/repo or full URL)",
            value=existing.github_repo or "" if existing else "",
        )
    elif tool_type == "apps_script":
        bold_line("Google Sheets / Apps Script")
        sheet_url = st.text_input(
            "Google Sheet URL *",
            value=existing.sheet_url or "" if existing else "",
        )
        github_repo = st.text_input(
            "GitHub repo (optional, recommended)",
            value=existing.github_repo or "" if existing else "",
            help="Link a repo if you version the script outside the sheet.",
        )

    future_plans_path = st.text_input(
        "Future plans path in GitHub repo (when using a repo)",
        value=existing.future_plans_path if existing else "docs/future_plans.md",
    )

    bold_line("Documentation", required=True)
    rich(
        f"README: paste content from your GitHub README.md {bold('or')} from the "
        f"{bold('first tab')} of your Apps Script sheet. Future plans: repo "
        "<code>docs/future_plans.md</code> or an equivalent sheet tab."
    )
    readme_fallback = st.text_area(
        "README.md *",
        value=existing.readme_fallback or "" if existing else "",
        height=180,
        placeholder="# My tool\n\nWhat it does, how to run it...",
    )
    future_plans_fallback = st.text_area(
        "future_plans.md *",
        value=existing.future_plans_fallback or "" if existing else "",
        height=180,
        placeholder="# Roadmap\n\n- Next sprint: ...",
    )

    bold_line("Infrastructure checklist", required=True)
    existing_check = existing.infra_checklist if existing else {}
    checklist: dict[str, bool] = {}
    checklist["has_ci_cd"] = st.checkbox(
        "CI/CD integrated",
        value=existing_check.get("has_ci_cd", False),
    )
    checklist["has_tests"] = st.checkbox(
        "Automated tests",
        value=existing_check.get("has_tests", False),
    )

    submitted = st.form_submit_button("Save tool" if existing else "Register tool", type="primary")

selected_tags = st.session_state[tags_key]

if submitted:
    errors = []
    if not name.strip():
        errors.append("Tool name is required.")
    if not short_desc.strip():
        errors.append("Short description is required.")
    if not submitter_name.strip():
        errors.append("Your name is required.")
    if not selected_tags:
        errors.append("Add at least one use case hashtag.")
    if not readme_fallback.strip():
        errors.append("README.md content is required.")
    if not future_plans_fallback.strip():
        errors.append("future_plans.md content is required.")

    if tool_type == "streamlit":
        if not app_url.strip():
            errors.append("Streamlit app URL is required.")
        if not github_repo.strip():
            errors.append("GitHub repo is required for Streamlit tools.")
    elif tool_type == "github_only":
        if not github_repo.strip():
            errors.append("GitHub repo is required.")
    elif tool_type == "apps_script":
        if not sheet_url.strip():
            errors.append("Google Sheet URL is required.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        for key in INFRA_CHECKLIST_KEYS:
            if not checklist.get(key):
                st.warning(INFRA_RECOMMENDATIONS.get(key, "Consider improving this before production."))

        payload = {
            "name": name.strip(),
            "short_desc": short_desc.strip(),
            "submitter_name": submitter_name.strip(),
            "submitter_email": submitter_email.strip(),
            "tool_type": tool_type,
            "app_url": app_url.strip() or None,
            "github_repo": github_repo.strip() or None,
            "sheet_url": sheet_url.strip() or None,
            "use_case_tags": selected_tags,
            "cluster_id": None,
            "future_plans_path": future_plans_path.strip() or "docs/future_plans.md",
            "infra_checklist": checklist,
            "readme_fallback": readme_fallback.strip(),
            "future_plans_fallback": future_plans_fallback.strip(),
        }
        if existing:
            update_tool(existing.id, payload)
            st.success("Tool updated!")
            st.query_params["tool"] = existing.id
            st.switch_page(DETAIL_SCRIPT)
        else:
            tool = create_tool(payload)
            st.success(f"Registered {tool.name}!")
            st.query_params["tool"] = tool.id
            st.switch_page(DETAIL_SCRIPT)
