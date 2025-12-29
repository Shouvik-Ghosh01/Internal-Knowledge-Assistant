from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class LocatorChunk:
	"""A single locator knowledge chunk.

	We store the final chunk text (what gets embedded) plus a few helpful fields
	that are written into vector metadata for filtering/debugging.
	"""

	text: str
	source: str
	page: str | None
	locator_name: str | None
	keyword: str | None


def _norm_text(value: Any) -> str:
	"""Normalize a cell value into clean single-line text.

	- Converts None/NaN-like values to empty string
	- Collapses whitespace/newlines
	- Treats common placeholders like '-', 'N/A' as empty
	"""

	if value is None:
		return ""
	s = str(value)
	if s.lower() in {"nan", "none"}:
		return ""
	s = " ".join(s.replace("\r", " ").replace("\n", " ").split())
	if s in {"-", "N/A", "NA"}:
		return ""
	return s.strip()


def _norm_col(col: Any) -> str:
	"""Normalize column names for matching (case/whitespace-insensitive)."""
	return " ".join(str(col).strip().lower().split())


def _pick_col(columns: Iterable[str], aliases: list[str]) -> str | None:
	"""Find the first column in `columns` matching any alias (normalized)."""
	cols = list(columns)
	for alias in aliases:
		alias_norm = _norm_col(alias)
		for c in cols:
			if _norm_col(c) == alias_norm:
				return c
	return None


def build_locator_chunks(xlsx_path: str | Path) -> list[LocatorChunk]:
	"""Convert a cleaned locator Excel into row-level chunks.

	This is a pure transformation step (Excel -> `LocatorChunk[]`) and can be
	used for debugging/inspection without touching Pinecone.
	"""

	try:
		import pandas as pd
	except Exception as exc:  # pragma: no cover
		raise RuntimeError(
			"pandas is required to ingest .xlsx files. Install with `pip install pandas openpyxl`."
		) from exc

	path = Path(xlsx_path)
	if not path.exists():
		return []

	tables: dict[str, Any] = pd.read_excel(path, sheet_name=None, dtype=str)
	chunks: list[LocatorChunk] = []
	seen: set[str] = set()

	for sheet_name, table in tables.items():
		if table is None or getattr(table, "empty", False):
			continue

		# Basic cleaning:
		# - Drop index-like columns (Unnamed: ...)
		# - Drop fully empty rows
		table = table.copy()
		table.columns = [str(c) for c in table.columns]
		table = table.loc[:, [c for c in table.columns if not _norm_col(c).startswith("unnamed")]]
		table = table.dropna(how="all")
		if table.empty:
			continue

		# Column mapping:
		# The cleaned file should have Locator/Keyword/Code/Description, but in case
		# names differ slightly, we accept common aliases.
		#
		# NOTE: The provided workbook contains multiple sheets (e.g. Common_Keywords,
		# Keywords, Common_Locators) with different header names. That's why the
		# alias list below is intentionally broad.

		# This Excel has multiple sheets with different headers (e.g. Common_Keywords, Common_Locators).
		# So we match a wider set of aliases.
		locator_col = _pick_col(
			table.columns,
			[
				"locator",
				"locator name",
				"label of locators",
				"element",
				"name",
			],
		)
		keyword_col = _pick_col(
			table.columns,
			[
				"keyword",
				"keywords",
				"keyword names",
				"key",
				"token",
			],
		)
		code_col = _pick_col(
			table.columns,
			[
				"code",
				"code snippet",
				"function of keyword / example usage",
				"function of  keyword / example usage",
				"path of loactors",
				"path of locators",
				"path",
				"xpath",
				"css",
				"selector",
				"id",
			],
		)
		desc_col = _pick_col(
			table.columns,
			[
				"description",
				"desc",
				"purpose of locators",
				"purpose of keyword",
				"purpose of keywords",
				"purpose",
				"remarks",
				"notes",
			],
		)

		for _, row in table.iterrows():
			# Extract fields (missing columns become empty strings).
			locator_name = _norm_text(row[locator_col]) if locator_col else ""
			keyword = _norm_text(row[keyword_col]) if keyword_col else ""
			code = _norm_text(row[code_col]) if code_col else ""
			description = _norm_text(row[desc_col]) if desc_col else ""

			# Fallback: if we couldn't map the columns well, still create a chunk
			# from any non-empty cells in the row (keeps ingestion resilient to header variations).
			#
			# This prevents the "0 chunks" issue when the Excel headers don't match our
			# expected names but the sheet still contains meaningful text.
			if not (locator_name or keyword or code or description):
				fallback_lines: list[str] = []
				for c in table.columns:
					v = _norm_text(row.get(c))
					if v:
						fallback_lines.append(f"{c}: {v}")
				if fallback_lines:
					code = "\n".join(fallback_lines)

			if not (locator_name or keyword or code or description):
				continue

			# Prefer at least locator/keyword to avoid embedding pure noise.
			# This keeps our vectors meaningful for retrieval.
			if not (locator_name or keyword):
				# If we only have fallback content (e.g., a row of notes), keep it only
				# when it looks non-trivial.
				if not code or len(code) < 10:
					continue

			chunk_text = (
				"\n".join(
					[
						"Document Type: UI Locator Reference",
						f"Sheet: {sheet_name}",
						f"Locator Name: {locator_name}",
						f"Keyword: {keyword}",
						f"Code Snippet: {code}",
						f"Description: {description}",
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
				LocatorChunk(
					text=chunk_text,
					source=str(path.as_posix()),
					page=str(sheet_name),
					locator_name=locator_name or None,
					keyword=keyword or None,
				)
			)

	return chunks


def ingest_common_keyword_locators(
	xlsx_path: str | Path = Path("data")
	/ "common_keywords_locators"
	/ "SAF_Common_Keywords_Locators_v1.0.xlsx",
	*,
	namespace: str | None = None,
	batch_size: int = 64,
) -> int:
	"""Reads the cleaned locators xlsx and upserts vectors to Pinecone.

	Pipeline:
	1) Build chunks from Excel rows (`build_locator_chunks`)
	2) Embed chunk text via `embed_texts`
	3) Upsert vectors to Pinecone index (`get_index().upsert`)
	"""

	from backend.rag.embeddings import embed_texts
	from backend.rag.pinecone_client import get_index

	chunks = build_locator_chunks(xlsx_path)
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
			# Stable-ish chunk id derived from file name + row index.
			chunk_id = f"locators::{Path(str(xlsx_path)).name}::{start + offset}"
			vectors.append(
				(
					chunk_id,
					embedding,
					{
						# 'text' is the retrievable content.
						"text": chunk.text,
						# 'source' and 'page' help show citations and debug retrieval.
						"source": chunk.source,
						"page": chunk.page,
						# Optional structured fields (nice for future filtering).
						"locator": chunk.locator_name,
						"keyword": chunk.keyword,
					},
				)
			)

		if namespace:
			index.upsert(vectors=vectors, namespace=namespace)
		else:
			index.upsert(vectors=vectors)
		upserted += len(vectors)

	return upserted
