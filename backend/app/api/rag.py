from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.services.rag_service import answer_question

router = APIRouter(prefix="/rag", tags=["rag"])


class RagAnswerRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


@router.post("/answer")
def create_rag_answer(
    request: RagAnswerRequest,
) -> dict[str, bool | int | float | str | None | list[dict[str, int | float | str]]]:
    return answer_question(request.question, top_k=request.top_k)
