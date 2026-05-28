"""Landing / home screen before sign-in."""

from __future__ import annotations

import streamlit as st

from lib.auth import render_oauth_config_errors, sync_user_from_streamlit_oidc
from lib.auth_bootstrap import auth_config_summary
from lib.personas import get_login_personas, persona_label


def apply_home_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        .home-wrap {
            max-width: 520px;
            margin: 4rem auto 2rem auto;
            text-align: center;
            padding: 2.5rem 2rem;
            border: 1px solid #4a4846;
            border-radius: 20px;
            background: linear-gradient(160deg, #3d3b39 0%, #343231 55%, #2e2c2b 100%);
        }
        .home-title {
            font-size: 2.35rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin: 0 0 0.5rem 0;
            color: #fafafa;
        }
        .home-sub {
            font-size: 1.05rem;
            color: #c8c6c4;
            margin: 0 0 1.75rem 0;
            line-height: 1.5;
        }
        .home-badge {
            display: inline-block;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #a8a6a4;
            margin-bottom: 1.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_home_shell(title: str, subtitle: str) -> None:
    apply_home_styles()
    st.markdown(
        f"""
        <div class="home-wrap">
            <p class="home-badge">Internal · NxtWave</p>
            <h1 class="home-title">{title}</h1>
            <p class="home-sub">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_google_home() -> None:
    """Branded home with Continue with Google → st.login()."""
    if render_oauth_config_errors():
        return

    _render_home_shell(
        "NxtWave Tool Library",
        "Discover, share, and launch internal AI tools built by your team.",
    )

    if sync_user_from_streamlit_oidc():
        st.rerun()

    _, btn_col, _ = st.columns([1, 1.2, 1])
    with btn_col:
        if st.button(
            "Continue with Google",
            type="primary",
            use_container_width=True,
            key="home_google_cta",
        ):
            try:
                st.login()
            except Exception as exc:
                st.error(f"Login failed: {exc}")
                summary = auth_config_summary()
                if summary:
                    with st.expander("Auth debug (no secrets shown)"):
                        st.json(summary)
                st.caption(
                    "On Streamlit Cloud, set **APP_PUBLIC_URL** and `[auth]` in **Settings → Secrets**, "
                    "then reboot. See `docs/DEPLOY_OAUTH.md`."
                )

    st.stop()


def show_persona_home(*, oauth_pending: bool = False) -> None:
    """Home-style screen for local test profiles."""
    subtitle = (
        "Google sign-in is not configured yet. Pick a test profile to explore the library."
        if oauth_pending
        else "Local test mode — choose a profile to explore the library."
    )
    _render_home_shell("NxtWave Tool Library", subtitle)

    if oauth_pending:
        st.info(
            "Add `client_id` and `client_secret` under `[auth]` in secrets, plus `APP_PUBLIC_URL` on Streamlit Cloud. "
            "See `docs/DEPLOY_OAUTH.md`."
        )

    _, form_col, _ = st.columns([1, 1.2, 1])
    with form_col:
        personas = get_login_personas()
        labels = [persona_label(p) for p in personas]
        default_idx = next(
            (i for i, p in enumerate(personas) if p["id"] == "teammate_1"),
            0,
        )
        picked_label = st.selectbox("Profile", labels, index=default_idx, key="home_persona_pick")
        picked = personas[labels.index(picked_label)]
        if st.button("Continue", type="primary", use_container_width=True, key="home_persona_cta"):
            from lib.auth import _set_user

            _set_user(picked["email"], picked["name"])
            st.session_state["active_persona_id"] = picked["id"]
            st.rerun()

    st.stop()
