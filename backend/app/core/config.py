import os
from pathlib import Path


def get_deepseek_api_key() -> str | None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()
    return None


def get_deepseek_base_url() -> str:
    return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")


def get_deepseek_model() -> str:
    return os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


def get_deepseek_timeout_seconds() -> float:
    configured_timeout = os.getenv("DEEPSEEK_TIMEOUT_SECONDS")
    if not configured_timeout:
        return 30.0
    return float(configured_timeout)


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
