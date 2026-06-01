import sqlite3
import os
import uuid
import json
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class SafeStaticFiles(StaticFiles):
    """Serve the web app but never expose the pose-api source directory."""

    async def get_response(self, path: str, scope):
        norm = path.replace("\\", "/").lstrip("/")
        if norm == "pose-api" or norm.startswith("pose-api/"):
            raise StarletteHTTPException(404)
        return await super().get_response(path, scope)

DB_PATH = os.environ.get("DB_PATH", "/data/pose.db" if os.path.isdir("/data") else "pose.db")
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = FastAPI(title="POSE API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── DB helpers ──────────────────────────────────────────────

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL DEFAULT 'party',
                name TEXT NOT NULL,
                date TEXT,
                time TEXT,
                location TEXT,
                description TEXT,
                host TEXT,
                style TEXT DEFAULT 'gradient',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rsvps (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                avatar INTEGER DEFAULT 1,
                answers TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                name TEXT NOT NULL,
                text TEXT NOT NULL,
                avatar INTEGER DEFAULT 1,
                reactions TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS updates (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            );
        """)
        # Add new columns if they don't exist (safe migration)
        migrations = [
            ("events", "poster", "TEXT DEFAULT ''"),
            ("events", "font", "TEXT DEFAULT 'grotesk'"),
            ("events", "kaspi", "TEXT DEFAULT ''"),
            ("events", "questions", "TEXT DEFAULT '[]'"),
            ("rsvps", "answers", "TEXT DEFAULT '{}'"),
        ]
        for table, col, coltype in migrations:
            try:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
            except Exception:
                pass


@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def gen_id():
    return uuid.uuid4().hex[:8]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ── Pydantic models ────────────────────────────────────────

class EventCreate(BaseModel):
    type: str = "party"
    name: str
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    host: Optional[str] = None
    style: str = "gradient"
    poster: str = ""
    font: str = "grotesk"
    kaspi: str = ""
    questions: List[str] = []


class RsvpCreate(BaseModel):
    name: str
    status: str = Field(pattern=r"^(going|maybe|cant)$")
    answers: dict = {}


class CommentCreate(BaseModel):
    name: str
    text: str


class ReactionToggle(BaseModel):
    emoji: str


class UpdateCreate(BaseModel):
    text: str


# ── Events ─────────────────────────────────────────────────

@app.post("/api/events")
def create_event(body: EventCreate):
    eid = gen_id()
    with get_db() as db:
        db.execute(
            "INSERT INTO events (id, type, name, date, time, location, description, host, style, poster, font, kaspi, questions, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, body.type, body.name, body.date, body.time, body.location, body.description, body.host, body.style, body.poster, body.font, body.kaspi, json.dumps(body.questions), now_iso()),
        )
    return {"id": eid}


@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    with get_db() as db:
        row = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")
        ev = dict(row)

        rsvps = [dict(r) for r in db.execute("SELECT * FROM rsvps WHERE event_id=? ORDER BY created_at", (event_id,)).fetchall()]
        comments = [dict(c) for c in db.execute("SELECT * FROM comments WHERE event_id=? ORDER BY created_at DESC", (event_id,)).fetchall()]
        for c in comments:
            c["reactions"] = json.loads(c["reactions"] or "{}")
        updates = [dict(u) for u in db.execute("SELECT * FROM updates WHERE event_id=? ORDER BY created_at DESC", (event_id,)).fetchall()]

        # Parse JSON fields
        ev["questions"] = json.loads(ev.get("questions") or "[]")
        for r in rsvps:
            r["answers"] = json.loads(r.get("answers") or "{}")
        ev["rsvps"] = rsvps
        ev["comments"] = comments
        ev["updates"] = updates
    return ev


# ── RSVPs ──────────────────────────────────────────────────

@app.post("/api/events/{event_id}/rsvps")
def add_rsvp(event_id: str, body: RsvpCreate):
    with get_db() as db:
        ev = db.execute("SELECT id FROM events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            raise HTTPException(404, "Event not found")
        rid = gen_id()
        db.execute(
            "INSERT INTO rsvps (id, event_id, name, status, avatar, answers, created_at) VALUES (?,?,?,?,?,?,?)",
            (rid, event_id, body.name, body.status, 1, json.dumps(body.answers), now_iso()),
        )
    return {"id": rid}


@app.delete("/api/rsvps/{rsvp_id}")
def delete_rsvp(rsvp_id: str):
    with get_db() as db:
        db.execute("DELETE FROM rsvps WHERE id=?", (rsvp_id,))
    return {"ok": True}


# ── Comments ───────────────────────────────────────────────

@app.post("/api/events/{event_id}/comments")
def add_comment(event_id: str, body: CommentCreate):
    with get_db() as db:
        ev = db.execute("SELECT id FROM events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            raise HTTPException(404, "Event not found")
        cid = gen_id()
        db.execute(
            "INSERT INTO comments (id, event_id, name, text, avatar, reactions, created_at) VALUES (?,?,?,?,?,?,?)",
            (cid, event_id, body.name, body.text, 1, "{}", now_iso()),
        )
    return {"id": cid}


@app.post("/api/comments/{comment_id}/reactions")
def toggle_reaction(comment_id: str, body: ReactionToggle):
    with get_db() as db:
        row = db.execute("SELECT reactions FROM comments WHERE id=?", (comment_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Comment not found")
        reactions = json.loads(row["reactions"] or "{}")
        current = reactions.get(body.emoji, 0)
        if current > 0:
            reactions[body.emoji] = current - 1
            if reactions[body.emoji] == 0:
                del reactions[body.emoji]
        else:
            reactions[body.emoji] = 1
        db.execute("UPDATE comments SET reactions=? WHERE id=?", (json.dumps(reactions), comment_id))
    return {"reactions": reactions}


# ── Updates (blast) ────────────────────────────────────────

@app.post("/api/events/{event_id}/updates")
def add_update(event_id: str, body: UpdateCreate):
    with get_db() as db:
        ev = db.execute("SELECT id FROM events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            raise HTTPException(404, "Event not found")
        uid = gen_id()
        db.execute(
            "INSERT INTO updates (id, event_id, text, created_at) VALUES (?,?,?,?)",
            (uid, event_id, body.text, now_iso()),
        )
    return {"id": uid}


# ── Health ─────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "db": DB_PATH}


@app.get("/api")
def api_root():
    return {"name": "POSE API", "version": "1.0.0", "docs": "/docs"}


# ── Init ───────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    init_db()


# ── Static frontend (served from parent pose/ directory) ───

if os.path.isdir(STATIC_DIR):
    app.mount("/", SafeStaticFiles(directory=STATIC_DIR, html=True), name="static")
