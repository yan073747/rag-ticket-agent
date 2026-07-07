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


class DocumentUploadTest(unittest.TestCase):
    def test_upload_text_document_saves_file_and_database_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            database_path = base_path / "app.db"
            upload_dir = base_path / "uploads"
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(database_path)
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(upload_dir)

            try:
                with TestClient(create_app()) as client:
                    response = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "company_policy.txt",
                                b"Refunds are handled within 7 business days.",
                                "text/plain",
                            )
                        },
                    )

                self.assertEqual(response.status_code, 201)
                payload = response.json()
                self.assertEqual(payload["filename"], "company_policy.txt")
                self.assertEqual(payload["file_path"], str(upload_dir / "company_policy.txt"))
                self.assertIsInstance(payload["id"], int)

                saved_file = upload_dir / "company_policy.txt"
                self.assertEqual(
                    saved_file.read_text(encoding="utf-8"),
                    "Refunds are handled within 7 business days.",
                )

                connection = sqlite3.connect(database_path)
                row = connection.execute(
                    "SELECT filename, file_path FROM documents WHERE id = ?",
                    (payload["id"],),
                ).fetchone()
                connection.close()

                self.assertEqual(
                    row,
                    ("company_policy.txt", str(upload_dir / "company_policy.txt")),
                )
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)

    def test_split_uploaded_document_saves_chunks_to_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            database_path = base_path / "app.db"
            upload_dir = base_path / "uploads"
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(database_path)
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(upload_dir)

            try:
                with TestClient(create_app()) as client:
                    upload_response = client.post(
                        "/documents/upload",
                        files={
                            "file": (
                                "faq.md",
                                b"Question A: Refunds take 7 days.\nQuestion B: Support replies in 24 hours.",
                                "text/markdown",
                            )
                        },
                    )
                    document_id = upload_response.json()["id"]

                    split_response = client.post(
                        f"/documents/{document_id}/chunks",
                        params={"chunk_size": 40, "chunk_overlap": 10},
                    )

                self.assertEqual(split_response.status_code, 201)
                payload = split_response.json()
                self.assertEqual(payload["document_id"], document_id)
                self.assertEqual(payload["chunk_count"], 3)
                self.assertEqual(len(payload["chunks"]), 3)
                self.assertEqual(payload["chunks"][0]["chunk_index"], 0)
                self.assertIn("Refunds take 7 days", payload["chunks"][0]["content"])

                connection = sqlite3.connect(database_path)
                rows = connection.execute(
                    """
                    SELECT chunk_index, content
                    FROM document_chunks
                    WHERE document_id = ?
                    ORDER BY chunk_index
                    """,
                    (document_id,),
                ).fetchall()
                connection.close()

                self.assertEqual(len(rows), 3)
                self.assertEqual(rows[0][0], 0)
                self.assertIn("Refunds take 7 days", rows[0][1])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)


if __name__ == "__main__":
    unittest.main()
