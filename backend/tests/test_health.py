import unittest
import os
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from app.main import app, create_app


class HealthEndpointTest(unittest.TestCase):
    def test_health_endpoint_returns_ok(self):
        client = TestClient(app)

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_app_startup_initializes_sqlite_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "startup.db"
            os.environ["RAG_AGENT_DATABASE_PATH"] = str(database_path)
            try:
                with TestClient(create_app()) as client:
                    response = client.get("/health")

                self.assertEqual(response.status_code, 200)
                self.assertTrue(database_path.exists())
            finally:
                os.environ.pop("RAG_AGENT_DATABASE_PATH", None)


if __name__ == "__main__":
    unittest.main()
