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


class TicketAdminTest(unittest.TestCase):
    def test_list_tickets_returns_created_low_confidence_ticket(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            base_path = Path(temp_dir)
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(base_path / "app.db")
            os.environ["RAG_AGENT_UPLOAD_DIR"] = str(base_path / "uploads")
            os.environ["RAG_AGENT_CHROMA_DIR"] = str(base_path / "chroma")

            try:
                with TestClient(create_app()) as client:
                    answer_response = client.post(
                        "/rag/answer",
                        json={"question": "How do I change my invoice address?", "top_k": 2},
                    )
                    ticket_id = answer_response.json()["ticket_id"]

                    tickets_response = client.get("/tickets")

                self.assertEqual(tickets_response.status_code, 200)
                tickets = tickets_response.json()["tickets"]
                self.assertEqual(len(tickets), 1)
                self.assertEqual(tickets[0]["id"], ticket_id)
                self.assertEqual(tickets[0]["question"], "How do I change my invoice address?")
                self.assertEqual(tickets[0]["status"], "open")
                self.assertIn("low confidence", tickets[0]["reason"])
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)
                os.environ.pop("RAG_AGENT_UPLOAD_DIR", None)
                os.environ.pop("RAG_AGENT_CHROMA_DIR", None)


if __name__ == "__main__":
    unittest.main()
