from pathlib import Path
from typing import Any

import chromadb

from app.services.embedding_service import embed_text

COLLECTION_NAME = "document_chunks"


def get_collection(chroma_dir: str | Path) -> Any:
    Path(chroma_dir).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def reset_vector_store(chroma_dir: str | Path) -> None:
    Path(chroma_dir).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        return


def index_chunks(chroma_dir: str | Path, chunks: list[dict[str, int | str]]) -> int:
    if not chunks:
        return 0

    collection = get_collection(chroma_dir)
    ids = [f"chunk-{chunk['id']}" for chunk in chunks]
    documents = [str(chunk["content"]) for chunk in chunks]
    embeddings = [embed_text(document) for document in documents]
    metadatas = [
        {
            "chunk_id": int(chunk["id"]),
            "document_id": int(chunk["document_id"]),
            "chunk_index": int(chunk["chunk_index"]),
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(chunks)


def search_chunks(chroma_dir: str | Path, query: str, top_k: int = 3) -> list[dict[str, int | float | str]]:
    collection = get_collection(chroma_dir)
    result = collection.query(
        query_embeddings=[embed_text(query)],
        n_results=max(top_k, 10),
        include=["documents", "metadatas", "distances"],
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    matches: list[dict[str, int | float | str]] = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        matches.append(
            {
                "document_id": int(metadata["document_id"]),
                "chunk_id": int(metadata["chunk_id"]),
                "chunk_index": int(metadata["chunk_index"]),
                "content": str(document),
                "distance": float(distance),
            }
        )

    return _rerank_chinese_matches(query, matches)[:top_k]


def _rerank_chinese_matches(
    query: str,
    matches: list[dict[str, int | float | str]],
) -> list[dict[str, int | float | str]]:
    query_features = _chinese_bigrams(query)
    if not query_features:
        return matches

    scored_matches: list[tuple[dict[str, int | float | str], float, float]] = []
    for match in matches:
        content_features = _chinese_bigrams(str(match["content"]))
        if not content_features:
            scored_matches.append((match, float(match["distance"]), 0.0))
            continue
        overlap = len(query_features & content_features) / len(query_features)
        adjusted_score = float(match["distance"]) - (overlap * 1.6)
        scored_matches.append((match, adjusted_score, overlap))

    if any(overlap > 0 for _, _, overlap in scored_matches):
        scored_matches = [
            scored_match
            for scored_match in scored_matches
            if scored_match[2] > 0
        ]

    return [
        match
        for match, _, _ in sorted(scored_matches, key=lambda scored_match: scored_match[1])
    ]


def _chinese_bigrams(text: str) -> set[str]:
    chinese_chars = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    if len(chinese_chars) < 2:
        return set()
    return {
        "".join(chinese_chars[index:index + 2])
        for index in range(len(chinese_chars) - 1)
    }
