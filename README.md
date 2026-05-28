# NxtWave AI Tools Marketplace

Internal Streamlit marketplace for AI tools built by the team. Browse the gallery without signing in; **register** a tool or **delete** a tool requires a sign-in.

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml -- at minimum set ADMIN_USERNAME / ADMIN_PASSWORD
streamlit run app.py
```

The app opens straight to the Gallery. Click **Sign in** in the sidebar (or **Register** > sign-in prompt) to reach the login page.

## Sign-in

The login page shows two buttons:

| Button | Who it's for | What it does |
|--------|---------------|---------------|
| **Continue with Google** | Anyone with an `@nxtwave.co.in` Google account | Uses Streamlit's native OIDC (`st.login()`). Domain enforced. |
| **Admin login** | App maintainers | Username + password from secrets. Admin can **delete tools**. |

Only **admin** can delete tools. Anyone signed in (Google or admin) can add and edit tools.

If the `[auth]` block is missing from secrets, the Google button is hidden — admin login still works. If `ADMIN_USERNAME` / `ADMIN_PASSWORD` are missing, the admin button is hidden.

## Listing your tool

1. Open **Register** in the sidebar (sign in if prompted).
2. Pick the tool type:
   - **Streamlit**: Streamlit app URL + GitHub repo (`org/repo`).
   - **GitHub-only**: repo link only.
   - **Apps Script**: Sheet URL (GitHub repo optional but recommended).
3. README + `future_plans.md` are required for the detail page tabs.
4. Pick at least one hashtag — the Gallery groups tools by hashtag.

### Repo convention (recommended)

```
your-repo/
  README.md
  docs/future_plans.md
```

When a GitHub repo is linked, the app fetches these files via the GitHub API and caches them for one hour.

## Secrets

| Key | Required? | Purpose |
|-----|-----------|---------|
| `ADMIN_USERNAME` | yes (for admin button) | Username for the admin login form |
| `ADMIN_PASSWORD` | yes (for admin button) | Password for the admin login form |
| `ALLOWED_EMAIL_DOMAINS` | optional | Comma-separated list. Defaults to `nxtwave.co.in` |
| `GITHUB_TOKEN` | optional | Read-only PAT so doc fetches aren't rate-limited |
| `[auth]` block | optional | Enables the Google sign-in button. See `.streamlit/secrets.toml.example` |

On **Streamlit Cloud**, paste the same keys into Settings → Secrets, then reboot the app.

## Data

SQLite database at `data/registry.db`, created on first run.
