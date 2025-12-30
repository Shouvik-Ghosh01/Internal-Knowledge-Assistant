from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PRReviewChunk:
	"""A single PR review checklist chunk.

	`text` is what we embed/store.
	`source` points to the original doc path for citations/debugging.
	`page` is the paragraph index (1-based) since DOCX doesn't have pages.
	"""

	text: str
	source: str
	page: str | None


def _norm_text(value: Any) -> str:
	"""Normalize paragraph/cell text into a clean single-line string."""

	if value is None:
		return ""
	s = str(value)
	if s.lower() in {"nan", "none"}:
		return ""
	return " ".join(s.replace("\r", " ").replace("\n", " ").split()).strip()


def build_pr_review_chunks(doc_path: str | Path, group_size: int = 3) -> list[PRReviewChunk]:
    from docx import Document

    path = Path(doc_path)
    if not path.exists():
        return []

    doc = Document(str(path))
    paragraphs = [
        _norm_text(p.text) for p in doc.paragraphs if _norm_text(p.text)
    ]

    chunks = []
    step = 0

    for i in range(0, len(paragraphs), group_size):
        group = paragraphs[i : i + group_size]
        step += 1

        chunk_text = (
            "Document Type: PR Review Checklist\n"
            f"Checklist Group {step}:\n"
            + "\n".join(f"- {g}" for g in group)
        )

        chunks.append(
            PRReviewChunk(
                text=chunk_text,
                source=str(path.as_posix()),
                page=str(step),
            )
        )

    return chunks

def ingest_pr_review(
	doc_path: str | Path = Path("data") / "pr_review" / "PR Review Checklist.docx",
	*,
	namespace: str | None = None,
	batch_size: int = 64,
) -> int:
	"""Reads the PR review checklist docx and upserts vectors to Pinecone."""

	from backend.rag.embeddings import embed_texts
	from backend.rag.pinecone_client import get_index

	chunks = build_pr_review_chunks(doc_path)
	if not chunks:
		return 0

	index = get_index()
	upserted = 0
	chunk_texts = [c.text for c in chunks]

	# Batch embeddings to keep requests reasonably sized.
	for start in range(0, len(chunks), max(1, batch_size)):
		batch_chunks = chunks[start : start + batch_size]
		batch_texts = chunk_texts[start : start + batch_size]
		embeddings = embed_texts(batch_texts)

		# Pinecone vector tuple format: (id, values, metadata)
		vectors = []
		for offset, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
			chunk_id = f"pr_review::{Path(str(doc_path)).name}::{start + offset}"
			vectors.append(
				(
					chunk_id,
					embedding,
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
