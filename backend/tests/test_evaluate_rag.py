import unittest
from datetime import datetime, timedelta, timezone
import os
import tempfile
from pathlib import Path

from scripts.evaluate_rag import (
    EvaluationCase,
    build_markdown_report,
    calculate_summary,
    evaluate_payload,
    load_env_file,
)


class RagEvaluationTest(unittest.TestCase):
    def test_evaluate_payload_passes_when_keywords_and_escalation_match(self):
        case = EvaluationCase(
            id="leave_policy",
            question="How many annual leave days?",
            expected_keywords=["10天", "年假"],
            should_escalate=False,
        )
        payload = {
            "answer": "员工每年可享受10天年假。",
            "confidence": 0.84,
            "sources": [{"document_id": 1}],
            "escalated_to_ticket": False,
        }

        result = evaluate_payload(case, payload)

        self.assertTrue(result.passed)
        self.assertEqual(result.missing_keywords, [])

    def test_evaluate_payload_fails_when_keyword_is_missing(self):
        case = EvaluationCase(
            id="expense_policy",
            question="How much is the hotel allowance?",
            expected_keywords=["350元", "100元"],
            should_escalate=False,
        )
        payload = {
            "answer": "住宿标准为350元。",
            "confidence": 0.76,
            "sources": [{"document_id": 1}],
            "escalated_to_ticket": False,
        }

        result = evaluate_payload(case, payload)

        self.assertFalse(result.passed)
        self.assertEqual(result.missing_keywords, ["100元"])

    def test_evaluate_payload_passes_escalation_case_without_keywords(self):
        case = EvaluationCase(
            id="unknown_revenue",
            question="What was 2024 revenue?",
            expected_keywords=[],
            should_escalate=True,
        )
        payload = {
            "answer": "未找到足够可靠的知识库内容，系统已创建工单。",
            "confidence": 0.39,
            "sources": [{"document_id": 1}, {"document_id": 2}],
            "escalated_to_ticket": True,
        }

        result = evaluate_payload(case, payload)

        self.assertTrue(result.passed)
        self.assertEqual(result.source_count, 2)

    def test_calculate_summary_returns_rates(self):
        results = [
            evaluate_payload(
                EvaluationCase("case_1", "q1", ["A"], False),
                {"answer": "A", "confidence": 0.8, "sources": [1, 2], "escalated_to_ticket": False},
            ),
            evaluate_payload(
                EvaluationCase("case_2", "q2", [], True),
                {"answer": "ticket", "confidence": 0.3, "sources": [1], "escalated_to_ticket": True},
            ),
        ]

        summary = calculate_summary(results)

        self.assertEqual(summary["total_cases"], 2)
        self.assertEqual(summary["passed_cases"], 2)
        self.assertEqual(summary["pass_rate"], 1.0)
        self.assertEqual(summary["keyword_hit_rate"], 1.0)
        self.assertEqual(summary["escalation_accuracy"], 1.0)
        self.assertEqual(summary["average_confidence"], 0.55)
        self.assertEqual(summary["average_source_count"], 1.5)

    def test_build_markdown_report_contains_summary_and_cases(self):
        result = evaluate_payload(
            EvaluationCase("case_1", "q1", ["A"], False),
            {"answer": "A", "confidence": 0.8, "sources": [1], "escalated_to_ticket": False},
        )

        report = build_markdown_report(
            [result],
            top_k=2,
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=timezone(timedelta(hours=8), name="CST"),
            ),
        )

        self.assertIn("# RAG Evaluation Report", report)
        self.assertIn("Pass rate: 100.0%", report)
        self.assertIn("| case_1 | yes | 80.0% | 1 | no | no | - |", report)

    def test_load_env_file_does_not_override_existing_environment(self):
        original_value = os.environ.get("DEEPSEEK_MODEL")
        original_timeout = os.environ.get("DEEPSEEK_TIMEOUT_SECONDS")
        os.environ["DEEPSEEK_MODEL"] = "existing-model"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                env_path = Path(temp_dir) / ".env"
                env_path.write_text(
                    "DEEPSEEK_MODEL=deepseek-v4-flash\n"
                    "DEEPSEEK_TIMEOUT_SECONDS=30\n",
                    encoding="utf-8",
                )

                load_env_file(env_path)

            self.assertEqual(os.environ["DEEPSEEK_MODEL"], "existing-model")
            self.assertEqual(os.environ["DEEPSEEK_TIMEOUT_SECONDS"], "30")
        finally:
            if original_value is None:
                os.environ.pop("DEEPSEEK_MODEL", None)
            else:
                os.environ["DEEPSEEK_MODEL"] = original_value
            if original_timeout is None:
                os.environ.pop("DEEPSEEK_TIMEOUT_SECONDS", None)
            else:
                os.environ["DEEPSEEK_TIMEOUT_SECONDS"] = original_timeout


if __name__ == "__main__":
    unittest.main()
