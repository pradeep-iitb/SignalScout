"""Uvicorn entrypoint for `uvicorn app.main:app` from the backend directory."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app

__all__ = ["app"]
