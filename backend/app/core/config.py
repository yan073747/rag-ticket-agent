import os
from pathlib import Path


def get_database_path() -> Path:
    configured_path = os.getenv("RAG_AGENT_DATABASE_PATH")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parents[2] / "data" / "app.db"


def get_upload_dir() -> Path:
    configured_path = os.getenv("RAG_AGENT_UPLOAD_DIR")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parents[2] / "uploads"


def get_chroma_dir() -> Path:
    configured_path = os.getenv("RAG_AGENT_CHROMA_DIR")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parents[2] / "data" / "chroma"
