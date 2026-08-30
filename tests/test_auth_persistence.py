from __future__ import annotations

from contextlib import closing
from pathlib import Path
from uuid import uuid4

from app.auth.auth import create_account, verify_credentials
from app.persistence.database import save_analysis_snapshot


def _test_db_path() -> Path:
    return Path("data") / f"auth_test_{uuid4().hex}.sqlite3"


def test_sqlite_account_creation_and_login(monkeypatch):
    database_path = _test_db_path()
    monkeypatch.setenv("SQLITE_DB_PATH", str(database_path))

    try:
        assert create_account("buyer@example.com", "Secure123") is None
        assert create_account("buyer@example.com", "Secure123") == "An account already exists for this email. Please log in instead."
        assert verify_credentials("buyer@example.com", "incorrect") == "Incorrect email or password."
        assert verify_credentials("buyer@example.com", "Secure123") is None
    finally:
        database_path.unlink(missing_ok=True)


def test_analysis_snapshot_is_saved(monkeypatch):
    database_path = _test_db_path()
    monkeypatch.setenv("SQLITE_DB_PATH", str(database_path))
    try:
        assert create_account("buyer@example.com", "Secure123") is None
        save_analysis_snapshot(
            user_email="buyer@example.com",
            project_id="proj_123",
            project_name="Procurement pilot",
            snapshot={"vendor_results": {"Vendor A": {"score": 85}}},
        )
        import sqlite3

        with closing(sqlite3.connect(database_path)) as connection:
            row = connection.execute(
                "SELECT project_name, snapshot_json FROM analysis_history WHERE user_email = ?", ("buyer@example.com",)
            ).fetchone()
        assert row[0] == "Procurement pilot"
        assert "Vendor A" in row[1]
    finally:
        database_path.unlink(missing_ok=True)
