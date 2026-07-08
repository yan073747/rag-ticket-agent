from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_database_path, get_upload_dir
from app.core.config import get_chroma_dir
from app.db.database import (
    create_document_record,
    get_document_chunks,
    get_document_record,
    replace_document_chunks,
)
from app.services.document_parser import (
    SUPPORTED_DOCUMENT_EXTENSIONS,
    DocumentParseError,
    parse_document_text,
)
from app.services.text_splitter import split_text
from app.services.vector_store import index_chunks

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = SUPPORTED_DOCUMENT_EXTENSIONS


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> dict[str, int | str]:
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if not filename or suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt, .md, .pdf and .docx files are supported.",
        )

    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / filename

    content = await file.read()
    saved_path.write_bytes(content)

    document_id = create_document_record(
        get_database_path(),
        filename=filename,
        file_path=str(saved_path),
    )

    return {
        "id": document_id,
        "filename": filename,
        "file_path": str(saved_path),
    }


@router.post("/{document_id}/chunks", status_code=status.HTTP_201_CREATED)
def split_document(
    document_id: int,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> dict[str, int | list[dict[str, int | str]]]:
    database_path = get_database_path()
    document = get_document_record(database_path, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    file_path = Path(str(document["file_path"]))
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found.",
        )

    try:
        chunks = split_text(
            parse_document_text(file_path),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    except (DocumentParseError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    saved_chunks = replace_document_chunks(database_path, document_id, chunks)

    return {
        "document_id": document_id,
        "chunk_count": len(saved_chunks),
        "chunks": saved_chunks,
    }


@router.post("/{document_id}/embeddings", status_code=status.HTTP_201_CREATED)
def index_document_embeddings(document_id: int) -> dict[str, int]:
    database_path = get_database_path()
    document = get_document_record(database_path, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    chunks = get_document_chunks(database_path, document_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no chunks. Split it before indexing embeddings.",
        )

    indexed_count = index_chunks(get_chroma_dir(), chunks)
    return {
        "document_id": document_id,
        "indexed_count": indexed_count,
    }
