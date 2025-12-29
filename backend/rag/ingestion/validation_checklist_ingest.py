from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ValidationChunk:
	"""A single validation checklist chunk.

	`text` is what we embed/store.
	`source` points to the original xlsx file.
	`page` stores the sheet name (since Excel doesn't have pages).
	"""

	text: str
	source: str
	page: str | None
	module: str | None
	rule: str | None


def _norm_text(value: Any) -> str:
	"""Normalize a cell value into clean single-line text."""

	if value is None:
		return ""
	s = str(value)
	if s.lower() in {"nan", "none"}:
		return ""
	s = " ".join(s.replace("\r", " ").replace("\n", " ").split()).strip()
	if s in {"-", "N/A", "NA"}:
		return ""
	return s


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


def build_validation_chunks(xlsx_path: str | Path) -> list[ValidationChunk]:
	"""Convert a cleaned validation checklist Excel into row-level chunks.

	This is a pure transformation step (Excel -> `ValidationChunk[]`) and can be
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
	chunks: list[ValidationChunk] = []
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
		# The validation workbook often has many "narrative" / checklist sheets where
		# headers don't match a single structured table.
		#
		# Strategy:
		# - Try best-effort mapping to {rule/module/expected/failure/...}
		# - If those columns don't exist, fall back to a generic row chunk:
		#   "Column: Value" lines for any non-empty cells.
		rule_col = _pick_col(table.columns, ["rule", "validation rule", "check", "scenario", "step", "steps"]) 
		module_col = _pick_col(table.columns, ["module", "screen", "section", "applies to"]) 
		expected_col = _pick_col(table.columns, ["expected", "expected result", "expected output", "expected outcome"]) 
		failure_col = _pick_col(table.columns, ["failure", "failure message", "message", "error message"]) 
		condition_col = _pick_col(table.columns, ["condition", "criteria", "when", "if"]) 
		severity_col = _pick_col(table.columns, ["severity", "priority", "p1/p2", "impact"]) 

		# If the sheet uses merged-cell style for module/section, forward-fill it.
		# (If your file is already cleaned, this is a harmless no-op.)
		ffill_cols = [c for c in [module_col] if c]
		if ffill_cols:
			table[ffill_cols] = table[ffill_cols].ffill()

		# If none of these key columns exist, treat each row as generic content.
		# This is what fixes the "0 chunks" issue for sheets like "Verifying ...".
		has_structured_cols = any([rule_col, expected_col, failure_col, condition_col, severity_col, module_col])

		for row_idx, row in table.iterrows():
			rule = _norm_text(row[rule_col]) if rule_col else ""
			module = _norm_text(row[module_col]) if module_col else ""
			expected = _norm_text(row[expected_col]) if expected_col else ""
			failure = _norm_text(row[failure_col]) if failure_col else ""
			condition = _norm_text(row[condition_col]) if condition_col else ""
			severity = _norm_text(row[severity_col]) if severity_col else ""

			# Generic fallback: turn any non-empty row into a chunk of "Column: Value" lines.
			# This ensures we still ingest useful content for sheets like "Verifying ...".
			if not has_structured_cols:
				row_lines: list[str] = []
				for c in table.columns:
					v = _norm_text(row.get(c))
					if v:
						row_lines.append(f"{c}: {v}")
				if not row_lines:
					continue

				chunk_text = (
					"\n".join(
						[
							"Document Type: Validation Checklist",
							f"Sheet: {sheet_name}",
							f"Row: {row_idx + 1}",
						]
					)
					+ "\n"
					+ "\n".join(row_lines).strip()
					+ "\n"
				)

				signature = " ".join(chunk_text.lower().split())
				if signature in seen:
					continue
				seen.add(signature)

				chunks.append(
					ValidationChunk(
						text=chunk_text,
						source=str(path.as_posix()),
						page=str(sheet_name),
						module=(module or sheet_name) or None,
						rule=None,
					)
				)
				continue

			# Skip rows that don't contain a meaningful rule.
			# We require at least a rule OR an expected result.
			if not (rule or expected):
				continue

			chunk_lines = [
				"Document Type: Validation Rule",
				f"Sheet: {sheet_name}",
			]
			if module:
				chunk_lines.append(f"Applies To: {module}")
			if condition:
				chunk_lines.append(f"Condition: {condition}")
			if rule:
				chunk_lines.append(f"Rule: {rule}")
			if expected:
				chunk_lines.append(f"Expected Result: {expected}")
			if failure:
				chunk_lines.append(f"Failure Message: {failure}")
			if severity:
				chunk_lines.append(f"Severity/Priority: {severity}")

			chunk_text = "\n".join(chunk_lines).strip() + "\n"

			# Deduplicate after normalization to reduce repeated vectors.
			signature = " ".join(chunk_text.lower().split())
			if signature in seen:
				continue
			seen.add(signature)

			chunks.append(
				ValidationChunk(
					text=chunk_text,
					source=str(path.as_posix()),
					page=str(sheet_name),
					module=module or None,
					rule=rule or None,
				)
			)

	return chunks


def ingest_validation_checklist(
	xlsx_path: str | Path = Path("data") / "validation_checklist" / "Report Verification Checklist.xlsx",
	*,
	namespace: str | None = None,
	batch_size: int = 64,
) -> int:
	"""Reads the validation checklist xlsx and upserts vectors to Pinecone.

	Pipeline:
	1) Build row-level chunks from Excel (`build_validation_chunks`)
	2) Embed chunk text via `embed_texts`
	3) Upsert vectors to Pinecone index (`get_index().upsert`)
	"""

	from backend.rag.embeddings import embed_texts
	from backend.rag.pinecone_client import get_index

	chunks = build_validation_chunks(xlsx_path)
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
			chunk_id = f"validation::{Path(str(xlsx_path)).name}::{start + offset}"
			# Pinecone metadata values cannot be null; drop any None/empty values.
			meta = {
				"text": chunk.text,
				"source": chunk.source,
				"page": chunk.page,
				"module": chunk.module,
				"rule": chunk.rule,
			}
			meta = {k: v for k, v in meta.items() if v is not None and v != ""}
			vectors.append(
				(
					chunk_id,
					embedding,
					meta,
				)
			)

		if namespace:
			index.upsert(vectors=vectors, namespace=namespace)
		else:
			index.upsert(vectors=vectors)
		upserted += len(vectors)

	return upserted
