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


class VectorStoreTest(unittest.TestCase):
    def test_index_document_chunks_and_search_with_chroma(self):
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
                                "support.md",
                                b"Refund policy: refunds take 7 days.\nWarranty policy: repairs take 14 days.",
                                "text/markdown",
                            )
                        },
                    )
                    document_id = upload_response.json()["id"]
                    client.post(
                        f"/documents/{document_id}/chunks",
                        params={"chunk_size": 45, "chunk_overlap": 5},
                    )

                    index_response = client.post(f"/documents/{document_id}/embeddings")
                    search_response = client.get(
                        "/search",
                        params={"query": "refund days", "top_k": 1},
                    )

                self.assertEqual(index_response.status_code, 201)
                self.assertEqual(index_response.json()["indexed_count"], 2)

                self.assertEqual(search_response.status_code, 200)
                results = search_response.json()["results"]
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["document_id"], document_id)
                self.assertIn("Refund policy", results[0]["content"])
                self.assertIsInstance(results[0]["distance"], float)
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)

    def test_chinese_search_reranks_matching_policy_above_unrelated_chunks(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(base_path / "app.db")
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    english_upload = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "sample_policy.txt",
                                b"Refunds are handled within 7 business days.",
                                "text/plain",
                            )
                        },
                    )
                    english_id = english_upload.json()["id"]
                    client.post(
                        f"/documents/{english_id}/chunks",
                        params={"chunk_size": 40, "chunk_overlap": 10},
                    )
                    client.post(f"/documents/{english_id}/embeddings")

                    chinese_upload = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "company_policy.txt",
                                "退款政策：客户提交退款申请后，客服会在 7 个工作日内完成处理。\n"
                                "发票政策：客户可以在订单完成后 30 天内申请开具发票。".encode("utf-8"),
                                "text/plain",
                            )
                        },
                    )
                    chinese_id = chinese_upload.json()["id"]
                    client.post(
                        f"/documents/{chinese_id}/chunks",
                        params={"chunk_size": 240, "chunk_overlap": 40},
                    )
                    client.post(f"/documents/{chinese_id}/embeddings")

                    search_response = client.get(
                        "/search",
                        params={"query": "什么时候可以开发票？", "top_k": 2},
                    )

                self.assertEqual(search_response.status_code, 200)
                results = search_response.json()["results"]
                self.assertEqual(len(results), 1)
                result = results[0]
                self.assertEqual(result["document_id"], chinese_id)
                self.assertIn("发票政策", result["content"])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)


if __name__ == "__main__":
    unittest.main()
