"""React-powered Streamlit component used as the application presentation shell.

All values passed into this component are display data. It only returns navigation
events; authentication, analysis, persistence, and scoring remain in Python.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_BUILD_DIR = Path(__file__).resolve().parents[2] / "frontend" / "build"
_shell = components.declare_component("vendorlens_shell", path=str(_BUILD_DIR))


def render_shell(page: str, user: str | None, metrics: list[dict[str, Any]] | None = None) -> dict[str, str] | None:
    """Render the compiled React shell and return its small navigation event."""
    if not _BUILD_DIR.exists():
        return None
    return _shell(page=page, user=user or "", metrics=metrics or [], default=None, key="vendorlens_react_shell")
