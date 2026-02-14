"""
SQLite models for Multiplayer Poke.
Manages users, teams, team membership, and calendar availability cache.
"""

import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.getenv("CORTEX_DB_PATH", str(Path(__file__).parent / "cortex.db"))

# ── Connection helper ─────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT,
            poke_api_key TEXT DEFAULT '',
            api_key     TEXT UNIQUE NOT NULL,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS teams (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            invite_code TEXT UNIQUE NOT NULL,
            created_by  TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS team_members (
            team_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role    TEXT NOT NULL DEFAULT 'member',
            joined_at TEXT NOT NULL,
            PRIMARY KEY (team_id, user_id),
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS availability_cache (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL,
            date_start TEXT NOT NULL,
            date_end   TEXT NOT NULL,
            busy_times TEXT NOT NULL DEFAULT '[]',
            synced_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_availability_user
            ON availability_cache(user_id, date_start, date_end);

        CREATE TABLE IF NOT EXISTS sync_tokens (
            token       TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            team_id     TEXT NOT NULL,
            date_start  TEXT NOT NULL,
            date_end    TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()
    print(f"SQLite database initialized at {DB_PATH}")


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(name: str, email: str = "", poke_api_key: str = "") -> dict:
    conn = _get_conn()
    user_id = str(uuid.uuid4())
    api_key = f"ctx_{secrets.token_hex(20)}"
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (id, name, email, poke_api_key, api_key, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, email, poke_api_key, api_key, now),
    )
    conn.commit()
    user = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
    conn.close()
    return user


def get_user_by_api_key(api_key: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_poke_key(user_id: str, poke_api_key: str) -> bool:
    conn = _get_conn()
    conn.execute("UPDATE users SET poke_api_key = ? WHERE id = ?", (poke_api_key, user_id))
    conn.commit()
    changed = conn.total_changes > 0
    conn.close()
    return changed


# ── Team CRUD ─────────────────────────────────────────────────────────────────

def create_team(name: str, created_by: str) -> dict:
    conn = _get_conn()
    team_id = str(uuid.uuid4())
    invite_code = secrets.token_hex(4).upper()  # 8-char hex code
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO teams (id, name, invite_code, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (team_id, name, invite_code, created_by, now),
    )
    # Creator auto-joins as admin
    conn.execute(
        "INSERT INTO team_members (team_id, user_id, role, joined_at) VALUES (?, ?, 'admin', ?)",
        (team_id, created_by, now),
    )
    conn.commit()
    team = dict(conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone())
    conn.close()
    return team


def get_team_by_id(team_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_team_by_invite_code(code: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM teams WHERE invite_code = ?", (code.upper(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def join_team(team_id: str, user_id: str, role: str = "member") -> bool:
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO team_members (team_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
            (team_id, user_id, role, now),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def get_team_members(team_id: str) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT u.id, u.name, u.email, u.poke_api_key, u.api_key, tm.role, tm.joined_at
        FROM team_members tm
        JOIN users u ON tm.user_id = u.id
        WHERE tm.team_id = ?
    """, (team_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_teams(user_id: str) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT t.*, tm.role
        FROM team_members tm
        JOIN teams t ON tm.team_id = t.id
        WHERE tm.user_id = ?
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_team_id(user_id: str) -> str | None:
    """Get the first team the user belongs to (for MCP context)."""
    teams = get_user_teams(user_id)
    return teams[0]["id"] if teams else None


# ── Availability Cache ────────────────────────────────────────────────────────

def store_availability(user_id: str, date_start: str, date_end: str, busy_times: list[dict]):
    """Store or update a user's availability for a date range."""
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    # Upsert: delete old entry for same range, insert new
    conn.execute(
        "DELETE FROM availability_cache WHERE user_id = ? AND date_start = ? AND date_end = ?",
        (user_id, date_start, date_end),
    )
    conn.execute(
        "INSERT INTO availability_cache (user_id, date_start, date_end, busy_times, synced_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, date_start, date_end, json.dumps(busy_times), now),
    )
    conn.commit()
    conn.close()


def get_availability(user_id: str, date_start: str, date_end: str) -> dict | None:
    """Get cached availability for a user and date range."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM availability_cache WHERE user_id = ? AND date_start = ? AND date_end = ?",
        (user_id, date_start, date_end),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["busy_times"] = json.loads(d["busy_times"])
        return d
    return None


def get_team_availability(team_id: str, date_start: str, date_end: str) -> dict[str, list[dict]]:
    """Get cached availability for all members of a team."""
    members = get_team_members(team_id)
    result: dict[str, list[dict]] = {}
    for m in members:
        avail = get_availability(m["id"], date_start, date_end)
        if avail:
            result[m["id"]] = avail["busy_times"]
    return result


# ── Sync Tokens (for Poke relay calendar sync) ────────────────────────────────

def create_sync_token(user_id: str, team_id: str, date_start: str, date_end: str) -> str:
    """Create a one-time sync token for a user to report calendar availability."""
    token = secrets.token_hex(12)
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO sync_tokens (token, user_id, team_id, date_start, date_end, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (token, user_id, team_id, date_start, date_end, now),
    )
    conn.commit()
    conn.close()
    return token


def consume_sync_token(token: str) -> dict | None:
    """Consume a sync token and return user_id, team_id, date_start, date_end. Deletes token."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM sync_tokens WHERE token = ?", (token,)).fetchone()
    if not row:
        conn.close()
        return None
    result = dict(row)
    conn.execute("DELETE FROM sync_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return result
