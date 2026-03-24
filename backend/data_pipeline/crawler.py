from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from datasets import load_dataset
from pymongo import UpdateOne

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
	sys.path.append(str(BACKEND_ROOT))

try:
	from db.mongo import MongoClientManager
	from utils.logger import get_logger
except ModuleNotFoundError:
	from backend.db.mongo import MongoClientManager
	from backend.utils.logger import get_logger

logger = get_logger(__name__)

DATASET_NAME = "th1nhng0/vietnamese-legal-documents"
CONTENT_CONFIG = "content"
METADATA_CONFIG = "metadata"


class LegalDatasetCrawler:
	"""Crawl legal content + metadata from Hugging Face and save to MongoDB."""

	def __init__(self, collection_name: str = "legal_documents", batch_size: int = 1000) -> None:
		self.collection_name = collection_name
		self.batch_size = batch_size
		self.mongo = MongoClientManager()

	@staticmethod
	def _build_document_id(split_name: str, row_index: int, metadata: dict[str, Any]) -> str:
		for key in ("id", "_id", "doc_id", "document_id", "uuid"):
			if key in metadata and metadata[key] is not None:
				return str(metadata[key])
		return f"{split_name}-{row_index}"

	def _flush(self, operations: list[UpdateOne]) -> None:
		if not operations:
			return
		result = self.collection.bulk_write(operations, ordered=False)
		logger.info(
			"Flushed batch to MongoDB: upserted=%s modified=%s matched=%s",
			result.upserted_count,
			result.modified_count,
			result.matched_count,
		)
		operations.clear()

	def run(self) -> int:
		self.mongo.ping()
		self.collection = self.mongo.get_collection(self.collection_name)
		self.collection.create_index("source_id", unique=True)

		logger.info("Loading dataset '%s' config '%s'", DATASET_NAME, CONTENT_CONFIG)
		content_ds = load_dataset(DATASET_NAME, CONTENT_CONFIG)

		logger.info("Loading dataset '%s' config '%s'", DATASET_NAME, METADATA_CONFIG)
		metadata_ds = load_dataset(DATASET_NAME, METADATA_CONFIG)

		total_saved = 0

		for split_name in content_ds.keys():
			if split_name not in metadata_ds:
				logger.warning("Split '%s' not found in metadata config. Skipping.", split_name)
				continue

			content_split = content_ds[split_name]
			metadata_split = metadata_ds[split_name]

			split_size = min(len(content_split), len(metadata_split))
			if len(content_split) != len(metadata_split):
				logger.warning(
					"Split '%s' has different sizes (content=%s, metadata=%s). Using min=%s",
					split_name,
					len(content_split),
					len(metadata_split),
					split_size,
				)

			logger.info("Processing split '%s' with %s records", split_name, split_size)

			operations: list[UpdateOne] = []

			for row_index in range(split_size):
				content_row = content_split[row_index]
				metadata_row = metadata_split[row_index]

				source_id = self._build_document_id(split_name, row_index, metadata_row)

				payload = {
					"source": "huggingface",
					"dataset": DATASET_NAME,
					"split": split_name,
					"source_id": source_id,
					"row_index": row_index,
					"content": content_row,
					"metadata": metadata_row,
				}

				operations.append(
					UpdateOne({"source_id": source_id}, {"$set": payload}, upsert=True)
				)

				if len(operations) >= self.batch_size:
					self._flush(operations)

			self._flush(operations)
			total_saved += split_size
			logger.info("Done split '%s'", split_name)

		logger.info("Finished ingestion. Total processed records: %s", total_saved)
		self.mongo.close()
		return total_saved


if __name__ == "__main__":
	crawler = LegalDatasetCrawler()
	crawler.run()
