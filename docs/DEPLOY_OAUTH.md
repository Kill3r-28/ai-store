# Google OAuth on Streamlit Cloud

## Why not `st.login()` / `/oauth2callback`?

Streamlit’s built-in OAuth callback (`/oauth2callback`) runs **outside your app code**. On Streamlit Cloud it often returns **Internal Server Error** after Google sign-in (token exchange / multi-instance state). This app uses **in-app OAuth** instead: Google redirects to your **app root** with `?code=...`, and `app.py` completes login.

## One-time Google Cloud setup

1. [Credentials](https://console.cloud.google.com/apis/credentials) → **OAuth 2.0 Client ID** → **Web application**.
2. **Authorized JavaScript origins**
   - `http://localhost:8501`
   - `https://nxtwave-ai-store.streamlit.app`
3. **Authorized redirect URIs** (app root — **not** `/oauth2callback`):
   - `http://localhost:8501/`
   - `https://nxtwave-ai-store.streamlit.app/`
4. OAuth consent screen: if **Testing**, add your `@nxtwave.co.in` user under **Test users**.

## Streamlit Cloud secrets

Copy [`streamlit-cloud-secrets.toml`](streamlit-cloud-secrets.toml) into **Settings → Secrets**.

| Key | Required | Notes |
|-----|----------|--------|
| `GOOGLE_CLIENT_ID` | Yes | Ends with `.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Yes | Starts with `GOCSPX-` |
| `OAUTH_STATE_SECRET` | Yes | Random string, 32+ chars |
| `APP_PUBLIC_URL` | Yes on Cloud | `https://nxtwave-ai-store.streamlit.app` |
| `DEV_SKIP_AUTH` | Yes | `"false"` in production |
| `[auth]` | **No** | **Remove** if present — it re-enables `/oauth2callback` |

After saving: **Reboot app**.

## Local development

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill GOOGLE_* keys; keep redirect in Google Console as http://localhost:8501/
streamlit run app.py
```

Verify credentials:

```bash
python scripts/verify_oauth.py
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Internal Server Error on `/oauth2callback` | Remove `[auth]` from Cloud secrets; use root redirect URIs in Google |
| `redirect_uri_mismatch` | Add exact URL from login **OAuth debug** expander to Google Console |
| `invalid_client` | Regenerate client secret; update Cloud secrets |
| Access restricted | Set `ALLOWED_EMAIL_DOMAINS = "nxtwave.co.in"` |
