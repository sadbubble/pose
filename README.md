# POSE

Free platform for creating invitations and managing events in Almaty.

The old backend on Fly.io (`pose-api-tyuhjdaa.fly.dev`) is no longer required.

**Want it on the web without running a server?** → see **[DEPLOY-FREE.md](DEPLOY-FREE.md)** (free Supabase + GitHub Pages / Netlify).

For local use, this repo runs **frontend + API together** on your machine.

## Quick start (Windows)

1. Install [Python 3.11+](https://www.python.org/downloads/).
2. Double-click `start.bat` or run:

```powershell
.\start.ps1
```

3. Open **http://127.0.0.1:8080** in your browser.

Data is stored in `pose/data/pose.db` (SQLite).

## Quick start (macOS / Linux)

```bash
cd pose/pose-api
python3 -m pip install -r requirements.txt
export DB_PATH="$(pwd)/../data/pose.db"
mkdir -p ../data
python3 -m uvicorn main:app --host 127.0.0.1 --port 8080 --reload
```

Open http://127.0.0.1:8080

## Deploy without Fly.io

### Option A — Docker (Railway, Render, any VPS)

```bash
docker build -t pose .
docker run -p 8080:8080 -v pose-data:/data pose
```

Set `DB_PATH=/data/pose.db` (default in the image). Open port 8080.

**Render:** New Web Service → Docker → connect repo → add a disk mount at `/data` if you want persistent SQLite.

**Railway:** Deploy from Dockerfile → add a volume at `/data` → set `DB_PATH=/data/pose.db`.

### Option B — Python only (no Docker)

On the server:

```bash
cd pose/pose-api
pip install -r requirements.txt
export DB_PATH=/var/lib/pose/pose.db
uvicorn main:app --host 0.0.0.0 --port 8080
```

Serve the whole app at your domain root (the API serves `index.html` and static files).

### Option C — Split hosting (static site + API)

1. Deploy the API as in Option A or B.
2. Host `pose/index.html` (and icons, `manifest.json`, `sw.js`) on Netlify, GitHub Pages, etc.
3. Copy `pose/config.js.example` to `pose/config.js` and set:

```javascript
var POSE_API_BASE = 'https://your-api-host.example.com';
```

Ensure CORS is already open (`*` in `main.py`).

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/events` | POST | Create event |
| `/api/events/{id}` | GET | Event + RSVPs + comments |
| `/docs` | GET | OpenAPI UI |

## Project layout

```
pose/
  index.html      # Frontend (Russian UI)
  config.js       # Optional API URL override
  pose-api/
    main.py       # FastAPI + SQLite
    requirements.txt
start.ps1         # Local dev (Windows)
Dockerfile        # Container deploy
```

## Troubleshooting

- **Blank page / API errors:** Use http://127.0.0.1:8080 (not `file://`). The integrated server serves both UI and API.
- **Old Fly.io URL:** Clear site data / unregister the service worker for the old domain, then reload.
- **Port in use:** Change `8080` in `start.ps1` and in the uvicorn command.
