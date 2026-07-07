import sqlite3
import json
from pathlib import Path


def initialize_database(database_path: str | Path) -> None:
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS qa_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL NOT NULL,
                sources TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def create_document_record(database_path: str | Path, filename: str, file_path: str) -> int:
    connection = sqlite3.connect(Path(database_path))
    try:
        cursor = connection.execute(
            "INSERT INTO documents (filename, file_path) VALUES (?, ?)",
            (filename, file_path),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_document_record(database_path: str | Path, document_id: int) -> dict[str, int | str] | None:
    connection = sqlite3.connect(Path(database_path))
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT id, filename, file_path FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "filename": str(row["filename"]),
            "file_path": str(row["file_path"]),
        }
    finally:
        connection.close()


def replace_document_chunks(
    database_path: str | Path,
    document_id: int,
    chunks: list[str],
) -> list[dict[str, int | str]]:
    connection = sqlite3.connect(Path(database_path))
    try:
        connection.execute(
            "DELETE FROM document_chunks WHERE document_id = ?",
            (document_id,),
        )
        saved_chunks: list[dict[str, int | str]] = []
        for index, content in enumerate(chunks):
            cursor = connection.execute(
                """
                INSERT INTO document_chunks (document_id, chunk_index, content)
                VALUES (?, ?, ?)
                """,
                (document_id, index, content),
            )
            saved_chunks.append(
                {
                    "id": int(cursor.lastrowid),
                    "document_id": document_id,
                    "chunk_index": index,
                    "content": content,
                }
            )
        connection.commit()
        return saved_chunks
    finally:
        connection.close()


def get_document_chunks(database_path: str | Path, document_id: int) -> list[dict[str, int | str]]:
    connection = sqlite3.connect(Path(database_path))
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT id, document_id, chunk_index, content
            FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index
            """,
            (document_id,),
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "document_id": int(row["document_id"]),
                "chunk_index": int(row["chunk_index"]),
                "content": str(row["content"]),
            }
            for row in rows
        ]
    finally:
        connection.close()


def create_qa_record(
    database_path: str | Path,
    question: str,
    answer: str,
    confidence: float,
    sources: list[dict[str, int | float | str]],
) -> int:
    connection = sqlite3.connect(Path(database_path))
    try:
        cursor = connection.execute(
            """
            INSERT INTO qa_records (question, answer, confidence, sources)
            VALUES (?, ?, ?, ?)
            """,
            (
                question,
                answer,
                confidence,
                json.dumps(sources, ensure_ascii=False),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def create_ticket_record(database_path: str | Path, question: str, reason: str) -> int:
    connection = sqlite3.connect(Path(database_path))
    try:
        cursor = connection.execute(
            "INSERT INTO tickets (question, reason) VALUES (?, ?)",
            (question, reason),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def list_ticket_records(database_path: str | Path) -> list[dict[str, int | str]]:
    connection = sqlite3.connect(Path(database_path))
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT id, question, status, reason, created_at
            FROM tickets
            ORDER BY id DESC
            """
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "question": str(row["question"]),
                "status": str(row["status"]),
                "reason": str(row["reason"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]
    finally:
        connection.close()


def list_document_records(database_path: str | Path) -> list[dict[str, int | str]]:
    connection = sqlite3.connect(Path(database_path))
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT id, filename, file_path, created_at
            FROM documents
            ORDER BY id DESC
            """
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "filename": str(row["filename"]),
                "file_path": str(row["file_path"]),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]
    finally:
        connection.close()


def list_qa_records(database_path: str | Path) -> list[dict[str, int | float | str | list]]:
    connection = sqlite3.connect(Path(database_path))
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT id, question, answer, confidence, sources, created_at
            FROM qa_records
            ORDER BY id DESC
            """
        ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "question": str(row["question"]),
                "answer": str(row["answer"]),
                "confidence": float(row["confidence"]),
                "sources": json.loads(str(row["sources"])),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]
    finally:
        connection.close()


def get_evaluation_metrics(
    database_path: str | Path,
    low_confidence_threshold: float,
) -> dict[str, float | int]:
    connection = sqlite3.connect(Path(database_path))
    try:
        total_documents = int(connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
        total_qa_records = int(connection.execute("SELECT COUNT(*) FROM qa_records").fetchone()[0])
        total_tickets = int(connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0])
        low_confidence_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM qa_records WHERE confidence < ?",
                (low_confidence_threshold,),
            ).fetchone()[0]
        )
        average_confidence_row = connection.execute(
            "SELECT AVG(confidence) FROM qa_records"
        ).fetchone()
        average_confidence = average_confidence_row[0] or 0.0

        escalation_rate = 0.0
        low_confidence_rate = 0.0
        if total_qa_records:
            escalation_rate = total_tickets / total_qa_records
            low_confidence_rate = low_confidence_count / total_qa_records

        return {
            "total_documents": total_documents,
            "total_qa_records": total_qa_records,
            "total_tickets": total_tickets,
            "low_confidence_count": low_confidence_count,
            "average_confidence": round(float(average_confidence), 4),
            "escalation_rate": round(escalation_rate, 4),
            "low_confidence_rate": round(low_confidence_rate, 4),
        }
    finally:
        connection.close()


def reset_demo_database(database_path: str | Path) -> None:
    connection = sqlite3.connect(Path(database_path))
    try:
        connection.executescript(
            """
            DELETE FROM document_chunks;
            DELETE FROM qa_records;
            DELETE FROM tickets;
            DELETE FROM documents;
            DELETE FROM sqlite_sequence
            WHERE name IN ('document_chunks', 'qa_records', 'tickets', 'documents');
            """
        )
        connection.commit()
    finally:
        connection.close()
