import json
import os
import sqlite3
import tempfile
import unittest
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from app.main import create_app


class RagAnswerTest(unittest.TestCase):
    def test_answer_question_with_sources_and_saved_qa_record(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            database_path = base_path / "app.db"
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(database_path)
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    upload_response = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "refund_policy.md",
                                b"Refund policy: refunds are handled within 7 business days.",
                                "text/markdown",
                            )
                        },
                    )
                    document_id = upload_response.json()["id"]
                    client.post(
                        f"/documents/{document_id}/chunks",
                        params={"chunk_size": 80, "chunk_overlap": 10},
                    )
                    client.post(f"/documents/{document_id}/embeddings")

                    answer_response = client.post(
                        "/rag/answer",
                        json={"question": "How long do refunds take?", "top_k": 2},
                    )

                self.assertEqual(answer_response.status_code, 200)
                payload = answer_response.json()
                self.assertEqual(payload["question"], "How long do refunds take?")
                self.assertIn("Refund policy", payload["answer"])
                self.assertGreater(payload["confidence"], 0)
                self.assertFalse(payload["escalated_to_ticket"])
                self.assertIsNone(payload["ticket_id"])
                self.assertEqual(len(payload["sources"]), 1)
                self.assertEqual(payload["sources"][0]["document_id"], document_id)
                self.assertEqual(payload["sources"][0]["chunk_index"], 0)

                connection = sqlite3.connect(database_path)
                row = connection.execute(
                    "SELECT question, answer, confidence, sources FROM qa_records"
                ).fetchone()
                ticket_count = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
                connection.close()

                self.assertEqual(row[0], "How long do refunds take?")
                self.assertIn("Refund policy", row[1])
                self.assertGreater(row[2], 0)
                self.assertEqual(json.loads(row[3])[0]["document_id"], document_id)
                self.assertEqual(ticket_count, 0)
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_chinese_invoice_question_answers_without_ticket(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            database_path = base_path / "app.db"
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(database_path)
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    upload_response = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "company_policy.txt",
                                "退款政策：客户提交退款申请后，客服会在 7 个工作日内完成处理。\n"
                                "发票政策：客户可以在订单完成后 30 天内申请开具发票。\n"
                                "人工客服：如果知识库无法回答问题，系统会自动创建工单交给人工处理。".encode("utf-8"),
                                "text/plain",
                            )
                        },
                    )
                    document_id = upload_response.json()["id"]
                    client.post(
                        f"/documents/{document_id}/chunks",
                        params={"chunk_size": 240, "chunk_overlap": 40},
                    )
                    client.post(f"/documents/{document_id}/embeddings")

                    answer_response = client.post(
                        "/rag/answer",
                        json={"question": "什么时候可以开发票？", "top_k": 2},
                    )

                self.assertEqual(answer_response.status_code, 200)
                payload = answer_response.json()
                self.assertFalse(payload["escalated_to_ticket"])
                self.assertIsNone(payload["ticket_id"])
                self.assertIn("发票政策", payload["answer"])
                self.assertIn("30 天", payload["answer"])
                self.assertNotIn("usiness days", payload["answer"])
                self.assertEqual(len(payload["sources"]), 1)
                self.assertGreaterEqual(payload["confidence"], 0.4)
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_answer_question_without_indexed_chunks_returns_low_confidence(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(base_path / "app.db")
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    answer_response = client.post(
                        "/rag/answer",
                        json={"question": "What is the vacation policy?", "top_k": 2},
                    )

                self.assertEqual(answer_response.status_code, 200)
                payload = answer_response.json()
                self.assertEqual(payload["confidence"], 0.0)
                self.assertEqual(payload["sources"], [])
                self.assertTrue(payload["escalated_to_ticket"])
                self.assertIsInstance(payload["ticket_id"], int)
                self.assertIn("未找到足够可靠", payload["answer"])

                connection = sqlite3.connect(base_path / "app.db")
                ticket_row = connection.execute(
                    "SELECT id, question, status, reason FROM tickets"
                ).fetchone()
                connection.close()

                self.assertEqual(ticket_row[0], payload["ticket_id"])
                self.assertEqual(ticket_row[1], "What is the vacation policy?")
                self.assertEqual(ticket_row[2], "open")
                self.assertIn("low confidence", ticket_row[3])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_answer_question_with_irrelevant_match_escalates_to_ticket(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(base_path / "app.db")
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    upload_response = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "refund_policy.md",
                                b"Refund policy: refunds are handled within 7 business days.",
                                "text/markdown",
                            )
                        },
                    )
                    document_id = upload_response.json()["id"]
                    client.post(
                        f"/documents/{document_id}/chunks",
                        params={"chunk_size": 80, "chunk_overlap": 10},
                    )
                    client.post(f"/documents/{document_id}/embeddings")

                    answer_response = client.post(
                        "/rag/answer",
                        json={"question": "What is the vacation policy?", "top_k": 2},
                    )

                self.assertEqual(answer_response.status_code, 200)
                payload = answer_response.json()
                self.assertLess(payload["confidence"], 0.4)
                self.assertTrue(payload["escalated_to_ticket"])
                self.assertIsInstance(payload["ticket_id"], int)
                self.assertIn("未找到足够可靠", payload["answer"])
                self.assertNotIn("Refund policy", payload["answer"])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_business_metrics_question_escalates_when_policy_docs_do_not_contain_facts(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(base_path / "app.db")
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    document_ids = []
                    for filename, content in [
                        (
                            "attendance_policy.txt",
                            "星辰科技有限公司员工考勤管理制度。第十六条 年假：入职满10年不满20年的，每年10天年假。",
                        ),
                        (
                            "expense_policy.txt",
                            "星辰科技有限公司财务报销管理制度。普通员工到上海出差，住宿标准350元，餐饮补贴100元/天。",
                        ),
                        (
                            "security_policy.txt",
                            "星辰科技有限公司信息安全管理制度。员工离职或调岗时，信息技术部在当日完成权限变更或账号注销。",
                        ),
                    ]:
                        upload_response = client.post(
                            "/documents/upload",
                            files={"file": (filename, content.encode("utf-8"), "text/plain")},
                        )
                        document_id = upload_response.json()["id"]
                        document_ids.append(document_id)
                        client.post(
                            f"/documents/{document_id}/chunks",
                            params={"chunk_size": 120, "chunk_overlap": 20},
                        )
                        client.post(f"/documents/{document_id}/embeddings")

                    answer_response = client.post(
                        "/rag/answer",
                        json={
                            "question": "星辰科技有限公司2024年的年度营收是多少？公司目前有多少名员工？",
                            "top_k": 2,
                        },
                    )

                self.assertEqual(answer_response.status_code, 200)
                payload = answer_response.json()
                self.assertLess(payload["confidence"], 0.4)
                self.assertTrue(payload["escalated_to_ticket"])
                self.assertIsInstance(payload["ticket_id"], int)
                self.assertIn("未找到足够可靠", payload["answer"])
                self.assertNotIn("信息安全管理制度", payload["answer"])
                self.assertNotIn("考勤管理制度", payload["answer"])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_address_and_shuttle_question_escalates_when_admin_facts_are_missing(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(base_path / "app.db")
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    upload_response = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "expense_policy.txt",
                                "星辰科技有限公司财务报销管理制度。费用报销须在费用发生后10个工作日内提交。",
                                "text/plain",
                            )
                        },
                    )
                    document_id = upload_response.json()["id"]
                    client.post(
                        f"/documents/{document_id}/chunks",
                        params={"chunk_size": 120, "chunk_overlap": 20},
                    )
                    client.post(f"/documents/{document_id}/embeddings")

                    answer_response = client.post(
                        "/rag/answer",
                        json={
                            "question": "星辰科技公司的办公地址在哪里？公司是否提供班车服务？班车的路线和时间安排是怎样的？",
                            "top_k": 2,
                        },
                    )

                self.assertEqual(answer_response.status_code, 200)
                payload = answer_response.json()
                self.assertLess(payload["confidence"], 0.4)
                self.assertTrue(payload["escalated_to_ticket"])
                self.assertIsInstance(payload["ticket_id"], int)
                self.assertIn("未找到足够可靠", payload["answer"])
                self.assertNotIn("财务报销管理制度", payload["answer"])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)


if __name__ == "__main__":
    unittest.main()
