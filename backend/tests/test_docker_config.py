from pathlib import Path
import unittest


class DockerConfigTest(unittest.TestCase):
    def test_dockerfile_copies_backend_and_frontend(self):
        project_root = Path(__file__).resolve().parents[2]
        dockerfile = project_root / "backend" / "Dockerfile"
        content = dockerfile.read_text(encoding="utf-8")

        self.assertIn("FROM python:3.11-slim", content)
        self.assertIn("COPY backend/requirements.txt", content)
        self.assertIn("COPY backend/app ./app", content)
        self.assertIn("COPY frontend ./frontend", content)
        self.assertIn("--host", content)
        self.assertIn("0.0.0.0", content)

    def test_compose_builds_from_project_root_and_persists_data(self):
        project_root = Path(__file__).resolve().parents[2]
        compose_file = project_root / "docker-compose.yml"
        content = compose_file.read_text(encoding="utf-8")

        self.assertIn("name: rag-ticket-agent", content)
        self.assertIn("context: .", content)
        self.assertIn("dockerfile: backend/Dockerfile", content)
        self.assertIn('"8000:8000"', content)
        self.assertIn("RAG_AGENT_DATABASE_PATH: /app/data/app.db", content)
        self.assertIn("./backend/data:/app/data", content)
        self.assertIn("./backend/uploads:/app/uploads", content)


if __name__ == "__main__":
    unittest.main()
