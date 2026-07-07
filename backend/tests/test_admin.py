import os
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


class AdminRecordsAndMetricsTest(unittest.TestCase):
    def test_admin_lists_documents_qa_records_and_metrics(self):
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
                    client.post(
                        "/rag/answer",
                        json={"question": "How long do refunds take?", "top_k": 2},
                    )
                    client.post(
                        "/rag/answer",
                        json={"question": "What is the vacation policy?", "top_k": 2},
                    )

                    documents_response = client.get("/admin/documents")
                    qa_response = client.get("/admin/qa-records")
                    metrics_response = client.get("/admin/metrics")

                self.assertEqual(documents_response.status_code, 200)
                documents = documents_response.json()["documents"]
                self.assertEqual(len(documents), 1)
                self.assertEqual(documents[0]["filename"], "refund_policy.md")

                self.assertEqual(qa_response.status_code, 200)
                qa_records = qa_response.json()["qa_records"]
                self.assertEqual(len(qa_records), 2)
                self.assertEqual(qa_records[0]["question"], "What is the vacation policy?")
                self.assertIn("sources", qa_records[0])

                self.assertEqual(metrics_response.status_code, 200)
                metrics = metrics_response.json()
                self.assertEqual(metrics["total_documents"], 1)
                self.assertEqual(metrics["total_qa_records"], 2)
                self.assertEqual(metrics["total_tickets"], 1)
                self.assertEqual(metrics["low_confidence_count"], 1)
                self.assertEqual(metrics["escalation_rate"], 0.5)
                self.assertGreater(metrics["average_confidence"], 0)
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_admin_metrics_returns_zero_values_for_empty_project(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(base_path / "app.db")
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    metrics_response = client.get("/admin/metrics")

                self.assertEqual(metrics_response.status_code, 200)
                self.assertEqual(
                    metrics_response.json(),
                    {
                        "total_documents": 0,
                        "total_qa_records": 0,
                        "total_tickets": 0,
                        "low_confidence_count": 0,
                        "average_confidence": 0.0,
                        "escalation_rate": 0.0,
                        "low_confidence_rate": 0.0,
                    },
                )
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_admin_reset_demo_clears_records_and_vector_index(self):
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
                                "invoice_policy.md",
                                "发票政策：客户可以在订单完成后 30 天内申请开具发票。".encode("utf-8"),
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
                    client.post(
                        "/rag/answer",
                        json={"question": "什么时候可以开发票？", "top_k": 2},
                    )
                    client.post(
                        "/rag/answer",
                        json={"question": "年假有多少天？", "top_k": 2},
                    )

                    self.assertGreater(client.get("/admin/metrics").json()["total_qa_records"], 0)
                    self.assertTrue(client.get("/search", params={"query": "开发票"}).json()["results"])

                    reset_response = client.post("/admin/reset-demo")

                    metrics_response = client.get("/admin/metrics")
                    documents_response = client.get("/admin/documents")
                    qa_response = client.get("/admin/qa-records")
                    tickets_response = client.get("/tickets")
                    search_response = client.get("/search", params={"query": "开发票"})

                self.assertEqual(reset_response.status_code, 200)
                self.assertEqual(reset_response.json(), {"reset": True})
                self.assertEqual(metrics_response.json()["total_documents"], 0)
                self.assertEqual(metrics_response.json()["total_qa_records"], 0)
                self.assertEqual(metrics_response.json()["total_tickets"], 0)
                self.assertEqual(documents_response.json()["documents"], [])
                self.assertEqual(qa_response.json()["qa_records"], [])
                self.assertEqual(tickets_response.json()["tickets"], [])
                self.assertEqual(search_response.json()["results"], [])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)


if __name__ == "__main__":
    unittest.main()
