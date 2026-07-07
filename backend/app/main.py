from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.documents import router as documents_router
from app.api.rag import router as rag_router
from app.api.search import router as search_router
from app.api.tickets import router as tickets_router
from app.core.config import get_database_path
from app.db.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database(get_database_path())
    yield


def create_app() -> FastAPI:
    api = FastAPI(
        title="Enterprise RAG Ticket Agent",
        description="Enterprise knowledge base RAG and customer support ticket agent.",
        version="0.1.0",
        lifespan=lifespan,
    )

    @api.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(documents_router)
    api.include_router(search_router)
    api.include_router(rag_router)
    api.include_router(tickets_router)
    api.include_router(admin_router)

    frontend_dir = find_frontend_dir(Path(__file__))
    if frontend_dir.exists():
        api.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return api


def find_frontend_dir(app_file: Path) -> Path:
    for parent in app_file.resolve().parents:
        frontend_dir = parent / "frontend"
        if frontend_dir.exists():
            return frontend_dir
    return app_file.resolve().parents[2] / "frontend"


app = create_app()
