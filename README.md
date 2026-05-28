# NxtWave AI Tools Marketplace

Internal Streamlit marketplace for AI tools built by the team: gallery, likes, ratings, README/roadmap from GitHub, comments, and infrastructure scorecards.

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# includes Authlib (required for Google sign-in via st.login)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml — for local dev set DEV_SKIP_AUTH = "true" (persona login: Teammate 1, etc.)
streamlit run app.py
```

## Listing your tool

1. Sign in with your NxtWave Google account (or use dev mode locally).
2. Open **Register a tool** and fill the form.
3. For **Streamlit** tools: Streamlit app URL + GitHub repo (`org/repo`).
4. For **GitHub-only** tools: repo link only.
5. For **Apps Script** tools: Sheet URL (GitHub repo optional but recommended) + required README/future_plans markdown.
6. Pick **hashtags** from the fixed list; the Gallery groups tools by hashtag.

### Repo convention (recommended)

```
your-repo/
  README.md                 # Shown on tool detail → README tab
  docs/future_plans.md      # Shown on Roadmap tab (customize path in form)
```

## Google OAuth (production)

See **[docs/DEPLOY_OAUTH.md](docs/DEPLOY_OAUTH.md)** for Streamlit Cloud secrets (copy-paste template).

1. Create a **Web application** OAuth client in Google Cloud Console.
2. Add redirect URIs: `http://localhost:8501/oauth2callback` and `https://<your-app>.streamlit.app/oauth2callback`
3. On **Streamlit Cloud**, paste secrets from `docs/streamlit-cloud-secrets.toml` (not the local gitignored file).
4. Set `APP_PUBLIC_URL`, `ALLOWED_EMAIL_DOMAINS`, and `DEV_SKIP_AUTH = "false"`.
5. Run `python scripts/verify_oauth.py` locally to validate credentials before deploy.

## Securing linked tools

Logging into this marketplace does **not** protect individual Streamlit apps or Sheets. Each tool should either:

- Use the same Google OAuth pattern on its deploy, or
- Sit behind your internal SSO / VPN / Cloudflare Access proxy.

## Environment variables

| Key | Purpose |
|-----|---------|
| `DEV_SKIP_AUTH` | `true` for local dev without OAuth |
| `ALLOWED_EMAIL_DOMAINS` | e.g. `nxtwave.com` |
| `ADMIN_EMAILS` | Comma-separated admins |
| `GITHUB_TOKEN` | Read-only PAT for doc sync |

## Data

SQLite database: `data/registry.db` (created on first run). Legacy `tools.json` is imported once if present.

## Pages

| Page | Description |
|------|-------------|
| Home (`app.py`) | Auth bootstrap; redirects to Gallery |
| Gallery | Main home — cards grouped by hashtag, filters |
| Tool detail | README, roadmap, launch, likes, comments, infra |
| Register | Add / edit your tools |
| Admin | Delete tools (ADMIN_EMAILS only) |
