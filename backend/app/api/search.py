from fastapi import APIRouter

from app.core.config import get_chroma_dir
from app.services.vector_store import search_chunks

router = APIRouter(tags=["search"])


@router.get("/search")
def search_documents(query: str, top_k: int = 3) -> dict[str, list[dict[str, int | float | str]]]:
    return {
        "results": search_chunks(
            get_chroma_dir(),
            query=query,
            top_k=top_k,
        )
    }
