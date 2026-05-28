# NxtWave AI Tools Marketplace

Internal Streamlit marketplace for AI tools built by the team: gallery, README/roadmap from GitHub, and infrastructure scorecards. No login — anyone with the URL can browse and register tools.

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens straight to the Gallery.

## Listing your tool

1. Open **Register** in the sidebar.
2. Pick the tool type:
   - **Streamlit**: Streamlit app URL + GitHub repo (`org/repo`).
   - **GitHub-only**: repo link only.
   - **Apps Script**: Sheet URL (GitHub repo optional but recommended).
3. Add your name (and optional email) so others know who submitted it.
4. Paste the README and a `future_plans.md` so the detail page is useful even before docs sync.
5. Pick at least one hashtag — the Gallery groups tools by hashtag.

### Repo convention (recommended)

```
your-repo/
  README.md                 # Shown on tool detail -> README tab
  docs/future_plans.md      # Shown on Roadmap tab (path is configurable)
```

When a GitHub repo is linked, the app fetches these files via the GitHub API and caches them for one hour.

## Optional secrets

| Key | Purpose |
|-----|---------|
| `GITHUB_TOKEN` | Read-only PAT so doc fetches are not rate-limited |

Set it in `.streamlit/secrets.toml` locally or in Streamlit Cloud -> Settings -> Secrets in production. See `.streamlit/secrets.toml.example`.

## Data

SQLite database at `data/registry.db`, created on first run.
