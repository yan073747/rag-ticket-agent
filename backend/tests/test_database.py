import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.db.database import initialize_database


class DatabaseInitializationTest(unittest.TestCase):
    def test_initialize_database_creates_core_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "app.db"

            initialize_database(database_path)

            connection = sqlite3.connect(database_path)
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            connection.close()

        table_names = {row[0] for row in rows}
        self.assertIn("documents", table_names)
        self.assertIn("document_chunks", table_names)
        self.assertIn("qa_records", table_names)
        self.assertIn("tickets", table_names)


if __name__ == "__main__":
    unittest.main()
