"""Test personas for local login when Google OAuth is not set up yet."""

from __future__ import annotations

TEST_PERSONAS: list[dict[str, str]] = [
    {
        "id": "teammate_1",
        "name": "Teammate 1",
        "email": "teammate1@nxtwave.co.in",
    },
]


def persona_label(p: dict[str, str]) -> str:
    return f"{p['name']} ({p['email']})"


def get_login_personas() -> list[dict[str, str]]:
    """Starter personas plus admin email from secrets (for testing admin flows)."""
    from lib.config import admin_emails

    out = list(TEST_PERSONAS)
    seen = {p["email"].lower() for p in out}
    for email in sorted(admin_emails()):
        if email not in seen:
            out.insert(
                0,
                {
                    "id": "admin_user",
                    "name": "Admin",
                    "email": email,
                },
            )
            seen.add(email)
    return out
