from app.core.config import get_chroma_dir, get_database_path
from app.db.database import create_qa_record, create_ticket_record
from app.services.llm_service import LLMServiceError, generate_rag_answer
from app.services.vector_store import search_chunks

LOW_CONFIDENCE_THRESHOLD = 0.4


def answer_question(
    question: str,
    top_k: int = 3,
) -> dict[str, bool | int | float | str | None | list[dict[str, int | float | str]]]:
    matches = search_chunks(get_chroma_dir(), query=question, top_k=top_k)
    sources = [
        {
            "document_id": int(match["document_id"]),
            "chunk_id": int(match["chunk_id"]),
            "chunk_index": int(match["chunk_index"]),
            "content": str(match["content"]),
            "distance": float(match["distance"]),
        }
        for match in matches
    ]

    if not sources:
        confidence = 0.0
    else:
        confidence = _distance_to_confidence(float(sources[0]["distance"]))
        confidence = _boost_chinese_confidence(question, sources, confidence)
        confidence = _cap_confidence_for_missing_required_facts(question, sources, confidence)

    ticket_id: int | None = None
    escalated_to_ticket = confidence < LOW_CONFIDENCE_THRESHOLD
    if escalated_to_ticket:
        answer = "未找到足够可靠的知识库内容，系统已创建工单，等待人工客服处理。"
        ticket_id = create_ticket_record(
            get_database_path(),
            question=question,
            reason=f"low confidence: {confidence}",
        )
    else:
        answer = _generate_answer_with_fallback(question, sources)

    qa_record_id = create_qa_record(
        get_database_path(),
        question=question,
        answer=answer,
        confidence=confidence,
        sources=sources,
    )

    return {
        "id": qa_record_id,
        "question": question,
        "answer": answer,
        "confidence": confidence,
        "sources": sources,
        "escalated_to_ticket": escalated_to_ticket,
        "ticket_id": ticket_id,
    }


def _generate_answer_with_fallback(
    question: str,
    sources: list[dict[str, int | float | str]],
) -> str:
    try:
        return generate_rag_answer(question, sources)
    except LLMServiceError:
        return _build_source_based_answer(sources)


def _build_source_based_answer(
    sources: list[dict[str, int | float | str]],
) -> str:
    context = "\n".join(
        f"[来源 {index + 1}] {source['content']}"
        for index, source in enumerate(sources)
    )
    return f"根据企业知识库内容，可以回答：\n{context}"


def _distance_to_confidence(distance: float) -> float:
    confidence = 1.0 / (1.0 + max(distance, 0.0))
    return round(confidence, 4)


def _boost_chinese_confidence(
    question: str,
    sources: list[dict[str, int | float | str]],
    current_confidence: float,
) -> float:
    question_features = _chinese_bigrams(question)
    if not question_features:
        return current_confidence

    best_overlap = 0.0
    for source in sources:
        source_features = _chinese_bigrams(str(source["content"]))
        if not source_features:
            continue
        overlap = len(question_features & source_features) / len(question_features)
        best_overlap = max(best_overlap, overlap)

    if best_overlap < 0.2:
        return current_confidence

    boosted_confidence = 0.42 + min(best_overlap, 0.5)
    return round(max(current_confidence, boosted_confidence), 4)


def _cap_confidence_for_missing_required_facts(
    question: str,
    sources: list[dict[str, int | float | str]],
    current_confidence: float,
) -> float:
    source_text = "\n".join(str(source["content"]) for source in sources)
    required_fact_groups = _required_fact_groups(question)
    if not required_fact_groups:
        return current_confidence

    for required_terms in required_fact_groups:
        if not any(term in source_text for term in required_terms):
            return min(current_confidence, LOW_CONFIDENCE_THRESHOLD - 0.01)

    return current_confidence


def _required_fact_groups(question: str) -> list[tuple[str, ...]]:
    groups: list[tuple[str, ...]] = []

    if any(term in question for term in ("营收", "营业收入", "营业额", "销售额")):
        groups.append(("营收", "营业收入", "营业额", "销售额", "收入数据"))

    if any(term in question for term in ("多少名员工", "员工人数", "员工总人数", "多少人")):
        groups.append(("员工人数", "员工总人数", "人员规模", "名员工", "现有员工"))

    if any(term in question for term in ("办公地址", "地址在哪里")):
        groups.append(("办公地址", "公司地址", "地址", "位于"))

    if "班车" in question:
        groups.append(("班车", "通勤车", "摆渡车"))

    return groups


def _chinese_bigrams(text: str) -> set[str]:
    chinese_chars = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    if len(chinese_chars) < 2:
        return set()
    return {
        "".join(chinese_chars[index:index + 2])
        for index in range(len(chinese_chars) - 1)
    }
