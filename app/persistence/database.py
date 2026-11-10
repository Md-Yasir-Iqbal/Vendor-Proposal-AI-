"""SQLite persistence isolated from UI and procurement evaluation code."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.utils.config import get_settings

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATABASE_PATH = _PROJECT_ROOT / "data" / "vendor_proposal_ai.sqlite3"


def _connection() -> sqlite3.Connection:
    # Supports a staged deployment where an older Settings class is still loaded.
    path = Path(getattr(get_settings(), "sqlite_db_path", str(_DEFAULT_DATABASE_PATH)))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with closing(_connection()) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE IF NOT EXISTS analysis_history (
                user_email TEXT NOT NULL,
                project_id TEXT NOT NULL,
                project_name TEXT,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_email, project_id),
                FOREIGN KEY (user_email) REFERENCES users(email)
            );
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                analysis_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_email, analysis_id, conversation_id)
            );
            CREATE INDEX IF NOT EXISTS idx_conversations_owner_analysis
                ON conversations(user_email, analysis_id, updated_at DESC);
            CREATE TABLE IF NOT EXISTS conversation_messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                citations_json TEXT NOT NULL DEFAULT '[]',
                tool_metadata_json TEXT NOT NULL DEFAULT '{}',
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id),
                UNIQUE(conversation_id, role, content_hash)
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_time
                ON conversation_messages(conversation_id, created_at ASC);
            """
        )


def get_user(email: str) -> dict[str, Any] | None:
    initialize_database()
    with closing(_connection()) as connection, connection:
        row = connection.execute(
            "SELECT email, password_salt, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row) if row else None


def create_user(email: str, password_salt: str, password_hash: str) -> bool:
    initialize_database()
    timestamp = _timestamp()
    try:
        with closing(_connection()) as connection, connection:
            connection.execute(
                "INSERT INTO users (email, password_salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (email, password_salt, password_hash, timestamp),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def update_last_login(email: str) -> None:
    initialize_database()
    with closing(_connection()) as connection, connection:
        connection.execute("UPDATE users SET last_login_at = ? WHERE email = ?", (_timestamp(), email))


def save_analysis_snapshot(user_email: str, project_id: str, project_name: str | None, snapshot: dict[str, Any]) -> None:
    """Upsert the current analysis snapshot for its signed-in owner."""
    if not user_email:
        return
    initialize_database()
    timestamp = _timestamp()
    payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
    with closing(_connection()) as connection, connection:
        connection.execute(
            """
            INSERT INTO analysis_history (user_email, project_id, project_name, snapshot_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_email, project_id) DO UPDATE SET
                project_name = excluded.project_name,
                snapshot_json = excluded.snapshot_json,
                updated_at = excluded.updated_at
            """,
            (user_email, project_id, project_name, payload, timestamp, timestamp),
        )


def list_analysis_history(user_email: str, limit: int = 8) -> list[dict[str, Any]]:
    """Return summary rows for the signed-in user's saved analyses."""
    if not user_email:
        return []
    initialize_database()
    with closing(_connection()) as connection, connection:
        rows = connection.execute(
            """
            SELECT project_id, project_name, created_at, updated_at
            FROM analysis_history
            WHERE user_email = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_email, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_analysis_snapshot(user_email: str, project_id: str) -> dict[str, Any] | None:
    """Retrieve one saved analysis only when it belongs to the signed-in user."""
    initialize_database()
    with closing(_connection()) as connection, connection:
        row = connection.execute(
            "SELECT snapshot_json FROM analysis_history WHERE user_email = ? AND project_id = ?",
            (user_email, project_id),
        ).fetchone()
    return json.loads(row["snapshot_json"]) if row else None


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Ask the Proposals conversation persistence -------------------------------------------

def create_conversation(user_email: str, analysis_id: str, conversation_id: str) -> None:
    initialize_database()
    now = _timestamp()
    with closing(_connection()) as connection, connection:
        connection.execute(
            "INSERT INTO conversations(conversation_id, user_email, analysis_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, user_email, analysis_id, now, now),
        )


def list_conversations(user_email: str, analysis_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with closing(_connection()) as connection:
        rows = connection.execute(
            "SELECT conversation_id, created_at, updated_at FROM conversations WHERE user_email = ? AND analysis_id = ? ORDER BY updated_at DESC",
            (user_email, analysis_id),
        ).fetchall()
    return [dict(row) for row in rows]


def get_or_create_analysis_conversation(user_email: str, analysis_id: str) -> str:
    """Return one stable chat per analysis; legacy duplicate chats stay hidden."""
    existing = list_conversations(user_email, analysis_id)
    if existing:
        return existing[0]["conversation_id"]
    import hashlib
    conversation_id = "conv_" + hashlib.sha256(f"{user_email}:{analysis_id}".encode("utf-8")).hexdigest()[:24]
    create_conversation(user_email, analysis_id, conversation_id)
    return conversation_id


def load_conversation_messages(user_email: str, conversation_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with closing(_connection()) as connection:
        rows = connection.execute(
            """SELECT m.message_id, m.role, m.content, m.citations_json, m.tool_metadata_json, m.created_at
               FROM conversation_messages m JOIN conversations c ON c.conversation_id = m.conversation_id
               WHERE c.user_email = ? AND c.conversation_id = ? ORDER BY m.created_at ASC""",
            (user_email, conversation_id),
        ).fetchall()
    return [{**dict(row), "citations": json.loads(row["citations_json"]), "tool_metadata": json.loads(row["tool_metadata_json"])} for row in rows]


def save_conversation_message(conversation_id: str, message_id: str, role: str, content: str, citations: list[dict[str, Any]] | None = None, tool_metadata: dict[str, Any] | None = None) -> bool:
    """Append a unique message and update its conversation timestamp."""
    import hashlib

    initialize_database()
    digest = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
    now = _timestamp()
    try:
        with closing(_connection()) as connection, connection:
            connection.execute(
                "INSERT INTO conversation_messages(message_id, conversation_id, role, content, citations_json, tool_metadata_json, content_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (message_id, conversation_id, role, content, json.dumps(citations or []), json.dumps(tool_metadata or {}), digest, now),
            )
            connection.execute("UPDATE conversations SET updated_at = ? WHERE conversation_id = ?", (now, conversation_id))
        return True
    except sqlite3.IntegrityError:
        return False


def clear_conversation(user_email: str, conversation_id: str) -> None:
    initialize_database()
    with closing(_connection()) as connection, connection:
        connection.execute(
            "DELETE FROM conversation_messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE conversation_id = ? AND user_email = ?)",
            (conversation_id, user_email),
        )
        connection.execute("UPDATE conversations SET updated_at = ? WHERE conversation_id = ? AND user_email = ?", (_timestamp(), conversation_id, user_email))
