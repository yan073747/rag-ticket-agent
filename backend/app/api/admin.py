from fastapi import APIRouter

from app.core.config import get_chroma_dir, get_database_path
from app.db.database import (
    get_evaluation_metrics,
    list_document_records,
    list_qa_records,
    reset_demo_database,
)
from app.services.rag_service import LOW_CONFIDENCE_THRESHOLD
from app.services.vector_store import reset_vector_store

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/documents")
def list_documents() -> dict[str, list[dict[str, int | str]]]:
    return {"documents": list_document_records(get_database_path())}


@router.get("/qa-records")
def list_question_answer_records() -> dict[str, list[dict[str, int | float | str | list]]]:
    return {"qa_records": list_qa_records(get_database_path())}


@router.get("/metrics")
def get_metrics() -> dict[str, float | int]:
    return get_evaluation_metrics(
        get_database_path(),
        low_confidence_threshold=LOW_CONFIDENCE_THRESHOLD,
    )


@router.post("/reset-demo")
def reset_demo() -> dict[str, bool]:
    reset_demo_database(get_database_path())
    reset_vector_store(get_chroma_dir())
    return {"reset": True}
