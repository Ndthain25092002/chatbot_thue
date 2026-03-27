from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from db.faiss_index import FaissIndex
from rag.embedder import Embedder


def _extract_text(record: Dict[str, Any]) -> str:
	"""Extract chunk text from dataset record."""
	content = record.get("content")
	if isinstance(content, dict):
		text = content.get("content")
		if isinstance(text, str):
			return text.strip()
		return ""
	if isinstance(content, str):
		return content.strip()
	return ""


def _build_metadata(record: Dict[str, Any], text: str, idx: int) -> Dict[str, Any]:
	"""Build searchable metadata for each vector."""
	meta = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
	legal_sectors = meta.get("legal_sectors")
	if isinstance(legal_sectors, list):
		legal_sectors = ", ".join(str(x) for x in legal_sectors)

	return {
		"chunk_id": str(record.get("source_id") or f"chunk-{idx+1}"),
		"content": text,
		"source": str(record.get("source") or "tax_fee_legal_documents"),
		"dataset": str(record.get("dataset") or ""),
		"doc_type": str(meta.get("legal_type") or ""),
		"title": str(meta.get("title") or ""),
		"issuer": str(meta.get("issuing_authority") or ""),
		"date": str(meta.get("issuance_date") or ""),
		"article": "",
		"clause": "",
		"point": "",
		"legal_sectors": str(legal_sectors or ""),
	}


def ingest_json_to_faiss(
	json_path: Path,
	batch_size: int = 32,
	max_records: int = 0,
	clear_index: bool = True,
) -> Dict[str, int]:
	"""Read JSON dataset, embed records, and index into FAISS."""
	records: List[Dict[str, Any]] = json.loads(json_path.read_text(encoding="utf-8"))
	if max_records > 0:
		records = records[:max_records]

	embedder = Embedder("intfloat/multilingual-e5-base")
	index = FaissIndex()
	if clear_index:
		index.clear()

	total = len(records)
	indexed = 0

	for start in range(0, total, batch_size):
		batch = records[start : start + batch_size]

		texts: List[str] = []
		metadatas: List[Dict[str, Any]] = []
		for offset, record in enumerate(batch):
			text = _extract_text(record)
			if not text:
				continue
			global_idx = start + offset
			texts.append(text)
			metadatas.append(_build_metadata(record, text, global_idx))

		if not texts:
			continue

		vectors = embedder.embed_documents(texts)
		index.add_documents(vectors, metadatas)
		indexed += len(vectors)

		print(f"Indexed {indexed}/{total} records")

	index.save()
	return {
		"total_records": total,
		"indexed_records": indexed,
		"faiss_size": index.get_size(),
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Ingest JSON records into FAISS index")
	parser.add_argument(
		"--json-path",
		default="data/tax_fee_legal_documents.json",
		help="Path to input JSON dataset",
	)
	parser.add_argument(
		"--batch-size",
		type=int,
		default=32,
		help="Embedding batch size",
	)
	parser.add_argument(
		"--max-records",
		type=int,
		default=0,
		help="Limit records for test run (0 = full dataset)",
	)
	parser.add_argument(
		"--append",
		action="store_true",
		help="Append to existing index instead of clearing it",
	)
	args = parser.parse_args()

	result = ingest_json_to_faiss(
		json_path=Path(args.json_path),
		batch_size=args.batch_size,
		max_records=args.max_records,
		clear_index=not args.append,
	)

	print("Ingestion completed")
	print(f"total_records={result['total_records']}")
	print(f"indexed_records={result['indexed_records']}")
	print(f"faiss_size={result['faiss_size']}")


if __name__ == "__main__":
	main()
