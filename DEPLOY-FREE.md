# Put POSE on the web for free (no VPS, no Docker)

You do **not** need Fly.io, Railway, or your own server.  
I cannot create accounts for you, but this path is about **5 minutes** and stays free.

## What you need

| Piece | Service | Cost |
|-------|---------|------|
| Database + API | [Supabase](https://supabase.com) | Free |
| Website files | GitHub Pages or Netlify | Free |

---

## Step 1 — Supabase (database, ~3 min)

1. Go to [supabase.com](https://supabase.com) → **Start your project** (GitHub or email login).
2. **New project** → pick a name and password → region closest to you → **Create**.
3. Open **SQL Editor** → **New query**.
4. Copy all of `supabase/schema.sql` from this repo → paste → **Run**.
5. Open **Project Settings** → **API**:
   - Copy **Project URL**
   - Copy **anon public** key (not `service_role`)

## Step 2 — Connect the app (~1 min)

1. In the `pose` folder, copy `config.js.example` → `config.js`.
2. Paste your URL and anon key:

```javascript
var POSE_SUPABASE_URL = 'https://xxxxx.supabase.co';
var POSE_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
```

## Step 3 — Put the site online

### Option A — GitHub Pages (recommended)

1. Create a repo on [github.com](https://github.com) (free).
2. Upload the **`pose`** folder contents (or push this whole project).
3. Repo **Settings** → **Pages** → Source: **GitHub Actions** (or deploy `pose` as root).
4. If you pushed the whole repo, enable the workflow in `.github/workflows/pages.yml` (already included).
5. Your site will be at `https://YOUR_USERNAME.github.io/YOUR_REPO/`

### Option B — Netlify Drop (fastest try)

1. Zip the **`pose`** folder (must include `config.js` with Supabase keys).
2. Open [app.netlify.com/drop](https://app.netlify.com/drop) and drag the zip.
3. You get a random URL like `https://random-name.netlify.app`.

### Option C — Still only on your PC

Run `start.bat` → open http://127.0.0.1:8080 (uses local SQLite, not Supabase).

---

## Optional: one-click server (if you prefer one URL for everything)

Push this repo to GitHub, then click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Uses `render.yaml` + Docker. Free tier sleeps after inactivity; first load may be slow.

---

## Security note

Supabase policies in `schema.sql` allow public read/write (same as the original open API). Fine for party invites; do not store secrets in events.

## Troubleshooting

- **“Error creating event”** — Check `config.js` keys and that `schema.sql` ran without errors.
- **Works locally but not online** — `config.js` must be in the deployed `pose` folder; it is not secret (anon key is public by design).
- **Old Fly.io errors** — Clear site data / unregister service worker for the old domain.
