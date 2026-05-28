# Google OAuth on Streamlit Cloud

## Important

- **Local** `.streamlit/secrets.toml` is gitignored and is **not** used by Streamlit Cloud.
- **Production** uses **Settings → Secrets** at [share.streamlit.io](https://share.streamlit.io) only.
- After any secret change: **Save → Reboot app**.

## One-time Google Cloud setup

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → **Create credentials** → **OAuth client ID** → **Web application**.
2. **Authorized JavaScript origins**
   - `http://localhost:8501`
   - `https://nxtwave-ai-store.streamlit.app`
3. **Authorized redirect URIs** (exact, no trailing slash on the path):
   - `http://localhost:8501/oauth2callback`
   - `https://nxtwave-ai-store.streamlit.app/oauth2callback`
4. OAuth consent screen: if **Testing**, add your `@nxtwave.co.in` account under **Test users**.

## Streamlit Cloud secrets (copy-paste)

Use the template in [`streamlit-cloud-secrets.toml`](streamlit-cloud-secrets.toml).

Critical fields:

| Key | Value |
|-----|--------|
| `APP_PUBLIC_URL` | `https://nxtwave-ai-store.streamlit.app` |
| `[auth].redirect_uri` | `https://nxtwave-ai-store.streamlit.app/oauth2callback` |
| `[auth].client_id` | From Google (ends with `.apps.googleusercontent.com`) |
| `[auth].client_secret` | From Google (starts with `GOCSPX-`) |
| `[auth].cookie_secret` | Random string, **32+ characters** |
| `DEV_SKIP_AUTH` | `"false"` |

`APP_PUBLIC_URL` forces the correct production `redirect_uri` even if `[auth].redirect_uri` was copied from a localhost template.

## Verify credentials locally

```bash
source venv/bin/activate
python scripts/verify_oauth.py
```

This checks secret shape and whether Google accepts your `client_id` / `client_secret` pair.

## If login still fails

1. Open **Manage app → Logs** right after the error.
2. On the login screen, expand **Auth debug** (shows `redirect_uri` and masked `client_id`).
3. Regenerate **client secret** in Google if it was ever pasted into chat or committed.
4. Confirm `requirements.txt` includes `Authlib>=1.3.2` and the deploy log shows it installed.

## Local development

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill [auth]; keep redirect_uri as http://localhost:8501/oauth2callback
# Do NOT set APP_PUBLIC_URL locally unless you intend to test production redirect.
streamlit run app.py
```

For persona login without Google: `DEV_SKIP_AUTH = "true"`.
