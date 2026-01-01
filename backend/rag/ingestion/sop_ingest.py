from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List


@dataclass(frozen=True)
class SOPChunk:
    text: str
    source: str
    page: str | None


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.lower() in {"nan", "none"}:
        return ""
    return " ".join(s.replace("\r", " ").replace("\n", " ").split()).strip()


def _is_heading(para) -> bool:
    """
    Heuristic heading detection:
    - Word style starts with 'Heading'
    - OR short uppercase lines
    """
    style = getattr(para.style, "name", "").lower()
    text = para.text.strip()

    if style.startswith("heading"):
        return True

    if text.isupper() and len(text.split()) <= 6:
        return True

    return False


def build_sop_chunks(doc_path: str | Path) -> list[SOPChunk]:
    from docx import Document

    path = Path(doc_path)
    if not path.exists():
        return []

    doc = Document(str(path))

    chunks: list[SOPChunk] = []
    seen: set[str] = set()

    current_heading = "General"
    buffer: List[str] = []
    section_index = 0

    def flush_buffer():
        nonlocal section_index, buffer

        if not buffer:
            return

        section_index += 1
        body = " ".join(buffer)
        buffer = []

        chunk_text = (
            "Document Type: SOP / Guidelines\n"
            f"Section: {current_heading}\n"
            f"{body}\n"
        )

        signature = " ".join(chunk_text.lower().split())
        if signature in seen:
            return
        seen.add(signature)

        chunks.append(
            SOPChunk(
                text=chunk_text,
                source=str(path.as_posix()),
                page=str(section_index),
            )
        )

    for para in doc.paragraphs:
        text = _norm_text(para.text)
        if not text:
            continue

        if _is_heading(para):
            # Finish previous section
            flush_buffer()
            current_heading = text
            continue

        buffer.append(text)

        # Flush when chunk reaches semantic size
        if len(" ".join(buffer)) >= 600:
            flush_buffer()

    # Flush remaining content
    flush_buffer()

    return chunks


def ingest_sop(
    doc_path: str | Path = Path("data") / "guidelines" / "Standard Operating procedure.docx",
    *,
    namespace: str | None = None,
    batch_size: int = 64,
) -> int:
    from backend.rag.embeddings import embed_texts
    from backend.rag.pinecone_client import get_index

    chunks = build_sop_chunks(doc_path)
    if not chunks:
        return 0

    index = get_index()
    upserted = 0

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        texts = [c.text for c in batch]
        embeddings = embed_texts(texts)

        vectors = []
        for offset, (chunk, emb) in enumerate(zip(batch, embeddings)):
            vectors.append(
                (
                    f"sop::{Path(doc_path).name}::{start + offset}",
                    emb,
                    {
                        "text": chunk.text,
                        "source": chunk.source,
                        "page": chunk.page,
                    },
                )
            )

        if namespace:
            index.upsert(vectors=vectors, namespace=namespace)
        else:
            index.upsert(vectors=vectors)

        upserted += len(vectors)

    return upserted