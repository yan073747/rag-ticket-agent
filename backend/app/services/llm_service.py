import json
import re
import urllib.error
import urllib.request

from app.core.config import (
    get_deepseek_api_key,
    get_deepseek_base_url,
    get_deepseek_model,
    get_deepseek_timeout_seconds,
)


class LLMServiceError(RuntimeError):
    pass


def is_llm_configured() -> bool:
    return get_deepseek_api_key() is not None


def generate_rag_answer(
    question: str,
    sources: list[dict[str, int | float | str]],
) -> str:
    api_key = get_deepseek_api_key()
    if not api_key:
        raise LLMServiceError("DEEPSEEK_API_KEY is not configured")

    request_body = {
        "model": get_deepseek_model(),
        "messages": [
            {
                "role": "system",
                "content": _build_system_prompt(),
            },
            {
                "role": "user",
                "content": _build_user_prompt(question, sources),
            },
        ],
        "temperature": 0.2,
    }

    request = urllib.request.Request(
        f"{get_deepseek_base_url()}/chat/completions",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=get_deepseek_timeout_seconds(),
        ) as response:
            response_body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LLMServiceError(f"DeepSeek request failed: {exc}") from exc

    try:
        answer = _strip_markdown_formatting(
            response_body["choices"][0]["message"]["content"].strip()
        )
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMServiceError("DeepSeek response does not contain answer text") from exc

    if not answer:
        raise LLMServiceError("DeepSeek returned an empty answer")
    return answer


def _strip_markdown_formatting(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
    cleaned = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\1", cleaned)
    cleaned = re.sub(r"(?<!_)_(?!_)(.*?)(?<!_)_(?!_)", r"\1", cleaned)
    cleaned = re.sub(r"^#{1,6}\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    return cleaned.strip()


def _build_system_prompt() -> str:
    return (
        "你是企业知识库客服 Agent。你只能根据用户提供的知识库片段回答，"
        "不能编造事实。若知识库片段不足以回答问题，请明确说明知识库没有足够信息。"
        "回答要简洁、清晰，并适合作为客服回复。"
        "请使用纯文本输出，不要使用 Markdown、星号加粗、标题符号或表格。"
    )


def _build_user_prompt(
    question: str,
    sources: list[dict[str, int | float | str]],
) -> str:
    context = "\n\n".join(
        f"[来源 {index + 1}]\n{source['content']}"
        for index, source in enumerate(sources)
    )
    return (
        f"用户问题：{question}\n\n"
        f"知识库片段：\n{context}\n\n"
        "请基于以上知识库片段回答，并保留必要的来源编号。"
        "输出为纯文本客服话术，不要使用 Markdown 符号。"
    )
