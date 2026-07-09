from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.rag_service import answer_question  # noqa: E402

CHINA_TIMEZONE = timezone(timedelta(hours=8), name="CST")


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    expected_keywords: list[str]
    should_escalate: bool


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    question: str
    answer: str
    confidence: float
    source_count: int
    expected_keywords: list[str]
    missing_keywords: list[str]
    expected_escalation: bool
    actual_escalation: bool
    passed: bool


def load_cases(path: Path) -> list[EvaluationCase]:
    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    cases: list[EvaluationCase] = []
    for raw_case in raw_cases:
        cases.append(
            EvaluationCase(
                id=str(raw_case["id"]),
                question=str(raw_case["question"]),
                expected_keywords=[str(keyword) for keyword in raw_case["expected_keywords"]],
                should_escalate=bool(raw_case["should_escalate"]),
            )
        )
    return cases


def evaluate_cases(cases: list[EvaluationCase], top_k: int) -> list[EvaluationResult]:
    results = []
    for case in cases:
        payload = answer_question(case.question, top_k=top_k)
        results.append(evaluate_payload(case, payload))
    return results


def evaluate_payload(
    case: EvaluationCase,
    payload: dict[str, object],
) -> EvaluationResult:
    answer = str(payload["answer"])
    actual_escalation = bool(payload["escalated_to_ticket"])
    missing_keywords = [
        keyword
        for keyword in case.expected_keywords
        if keyword not in answer
    ]
    escalation_matches = actual_escalation == case.should_escalate
    keyword_matches = case.should_escalate or not missing_keywords
    passed = escalation_matches and keyword_matches

    return EvaluationResult(
        case_id=case.id,
        question=case.question,
        answer=answer,
        confidence=float(payload["confidence"]),
        source_count=len(payload["sources"]),
        expected_keywords=case.expected_keywords,
        missing_keywords=missing_keywords,
        expected_escalation=case.should_escalate,
        actual_escalation=actual_escalation,
        passed=passed,
    )


def calculate_summary(results: list[EvaluationResult]) -> dict[str, float | int]:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.passed)
    keyword_cases = [result for result in results if result.expected_keywords]
    keyword_passed_cases = sum(1 for result in keyword_cases if not result.missing_keywords)
    escalation_correct_cases = sum(
        1
        for result in results
        if result.expected_escalation == result.actual_escalation
    )

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": _safe_ratio(passed_cases, total_cases),
        "keyword_hit_rate": _safe_ratio(keyword_passed_cases, len(keyword_cases)),
        "escalation_accuracy": _safe_ratio(escalation_correct_cases, total_cases),
        "average_confidence": round(mean([result.confidence for result in results]), 4)
        if results
        else 0.0,
        "average_source_count": round(mean([result.source_count for result in results]), 2)
        if results
        else 0.0,
    }


def build_markdown_report(
    results: list[EvaluationResult],
    top_k: int,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now(CHINA_TIMEZONE)
    summary = calculate_summary(results)
    lines = [
        "# RAG Evaluation Report",
        "",
        f"- Generated at: {generated_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- Top K: {top_k}",
        f"- Total cases: {summary['total_cases']}",
        f"- Passed cases: {summary['passed_cases']}",
        f"- Pass rate: {_format_percent(summary['pass_rate'])}",
        f"- Keyword hit rate: {_format_percent(summary['keyword_hit_rate'])}",
        f"- Escalation accuracy: {_format_percent(summary['escalation_accuracy'])}",
        f"- Average confidence: {_format_percent(summary['average_confidence'])}",
        f"- Average source count: {summary['average_source_count']}",
        "",
        "## Case Results",
        "",
        "| Case | Passed | Confidence | Sources | Expected Escalation | Actual Escalation | Missing Keywords |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for result in results:
        missing_keywords = ", ".join(result.missing_keywords) if result.missing_keywords else "-"
        lines.append(
            "| "
            f"{result.case_id} | "
            f"{'yes' if result.passed else 'no'} | "
            f"{_format_percent(result.confidence)} | "
            f"{result.source_count} | "
            f"{'yes' if result.expected_escalation else 'no'} | "
            f"{'yes' if result.actual_escalation else 'no'} | "
            f"{missing_keywords} |"
        )

    lines.extend(["", "## Details", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.case_id}",
                "",
                f"- Question: {result.question}",
                f"- Expected keywords: {', '.join(result.expected_keywords) if result.expected_keywords else '-'}",
                f"- Missing keywords: {', '.join(result.missing_keywords) if result.missing_keywords else '-'}",
                f"- Expected escalation: {'yes' if result.expected_escalation else 'no'}",
                f"- Actual escalation: {'yes' if result.actual_escalation else 'no'}",
                f"- Confidence: {_format_percent(result.confidence)}",
                f"- Source count: {result.source_count}",
                "",
                "Answer:",
                "",
                result.answer,
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def write_report(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue

        key, value = stripped_line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _format_percent(value: float | int) -> str:
    return f"{float(value) * 100:.1f}%"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batch evaluation for the RAG agent.")
    parser.add_argument(
        "--questions",
        type=Path,
        default=PROJECT_ROOT / "docs" / "evaluation" / "rag_eval_questions.json",
        help="Path to evaluation question JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "evaluation" / "evaluation_report.md",
        help="Path to write the Markdown evaluation report.",
    )
    parser.add_argument("--top-k", type=int, default=2, help="Number of chunks to retrieve.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(PROJECT_ROOT / ".env")
    cases = load_cases(args.questions)
    results = evaluate_cases(cases, top_k=args.top_k)
    report = build_markdown_report(results, top_k=args.top_k)
    write_report(args.output, report)
    summary = calculate_summary(results)
    print(f"Evaluation report written to {args.output}")
    print(f"Pass rate: {_format_percent(summary['pass_rate'])}")
    print(f"Escalation accuracy: {_format_percent(summary['escalation_accuracy'])}")
    return 0 if summary["passed_cases"] == summary["total_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
CHINA_TIMEZONE = timezone(timedelta(hours=8), name="CST")
