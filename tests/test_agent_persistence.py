from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.persistence.database import (
    clear_conversation,
    create_conversation,
    list_conversations,
    load_conversation_messages,
    save_conversation_message,
)


def test_conversations_are_isolated_by_analysis_and_preserve_metadata(monkeypatch):
    path = Path("data") / f"conversation_test_{uuid4().hex}.sqlite3"
    monkeypatch.setenv("SQLITE_DB_PATH", str(path))
    try:
        create_conversation("buyer@example.com", "analysis_a", "conv_a")
        create_conversation("buyer@example.com", "analysis_b", "conv_b")
        assert [row["conversation_id"] for row in list_conversations("buyer@example.com", "analysis_a")] == ["conv_a"]
        save_conversation_message("conv_a", "one", "user", "Which vendor is cheapest?")
        save_conversation_message("conv_a", "two", "assistant", "Vendor A is lowest.", [{"id": "E1"}], {"tools_used": ["calculate_total_cost"]})
        messages = load_conversation_messages("buyer@example.com", "conv_a")
        assert [item["role"] for item in messages] == ["user", "assistant"]
        assert messages[1]["citations"] == [{"id": "E1"}]
        assert messages[1]["tool_metadata"]["tools_used"] == ["calculate_total_cost"]
        clear_conversation("buyer@example.com", "conv_a")
        assert load_conversation_messages("buyer@example.com", "conv_a") == []
        assert list_conversations("buyer@example.com", "analysis_b")[0]["conversation_id"] == "conv_b"
    finally:
        path.unlink(missing_ok=True)
