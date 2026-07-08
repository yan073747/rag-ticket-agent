from pathlib import Path


class DocumentParseError(ValueError):
    pass


SUPPORTED_DOCUMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def parse_document_text(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        text = _parse_pdf(path)
    elif suffix == ".docx":
        text = _parse_docx(path)
    else:
        raise DocumentParseError(
            "Unsupported file type. Supported types: .txt, .md, .pdf, .docx."
        )

    if not text.strip():
        raise DocumentParseError("No readable text was found in this document.")

    return text


def _parse_pdf(file_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise DocumentParseError("PDF parsing dependency pypdf is not installed.") from error

    try:
        reader = PdfReader(str(file_path))
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except Exception as error:
        raise DocumentParseError("Failed to parse PDF document.") from error

    return "\n".join(page_texts)


def _parse_docx(file_path: Path) -> str:
    try:
        from docx import Document
    except ImportError as error:
        raise DocumentParseError("Word parsing dependency python-docx is not installed.") from error

    try:
        document = Document(str(file_path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
    except Exception as error:
        raise DocumentParseError("Failed to parse Word document.") from error

    return "\n".join(paragraphs)
