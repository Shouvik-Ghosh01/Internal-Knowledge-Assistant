from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SOPChunk:
	"""A single SOP chunk.

	`text` is what we embed/store.
	`source` is the doc path (for citations/debugging).
	`page` is the step/paragraph index (1-based) since DOCX isn't paginated.
	"""

	text: str
	source: str
	page: str | None


def _norm_text(value: Any) -> str:
	"""Normalize paragraph text into a clean single-line string."""

	if value is None:
		return ""
	s = str(value)
	if s.lower() in {"nan", "none"}:
		return ""
	return " ".join(s.replace("\r", " ").replace("\n", " ").split()).strip()


def build_sop_chunks(doc_path: str | Path) -> list[SOPChunk]:
	"""Convert an SOP DOCX into paragraph-level step chunks."""

	try:
		from docx import Document
	except Exception as exc:  # pragma: no cover
		raise RuntimeError(
			"python-docx is required to ingest .docx files. Install with `pip install python-docx`."
		) from exc

	path = Path(doc_path)
	if not path.exists():
		return []

	doc = Document(str(path))
	chunks: list[SOPChunk] = []
	seen: set[str] = set()
	step = 0

	for para in doc.paragraphs:
		text = _norm_text(getattr(para, "text", ""))
		if not text:
			continue

		step += 1
		chunk_text = (
			"\n".join(
				[
					"Document Type: SOP / Guidelines",
					f"Step {step}:",
					text,
				]
			).strip()
			+ "\n"
		)

		# Deduplicate after normalization to reduce repeated vectors.
		signature = " ".join(chunk_text.lower().split())
		if signature in seen:
			continue
		seen.add(signature)

		chunks.append(
			SOPChunk(
				text=chunk_text,
				source=str(path.as_posix()),
				page=str(step),
			)
		)

	return chunks


def ingest_sop(
	doc_path: str | Path = Path("data") / "guidelines" / "Standard Operating procedure.docx",
	*,
	namespace: str | None = None,
	batch_size: int = 64,
) -> int:
	"""Reads the SOP docx and upserts vectors to Pinecone.

	Pipeline:
	1) Build step chunks from DOCX paragraphs (`build_sop_chunks`)
	2) Embed chunk text via `embed_texts`
	3) Upsert vectors to Pinecone index (`get_index().upsert`)
	"""

	from backend.rag.embeddings import embed_texts
	from backend.rag.pinecone_client import get_index

	chunks = build_sop_chunks(doc_path)
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
			chunk_id = f"sop::{Path(str(doc_path)).name}::{start + offset}"
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
