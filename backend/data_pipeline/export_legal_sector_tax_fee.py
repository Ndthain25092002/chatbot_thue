from __future__ import annotations

import json
import sys
from pathlib import Path

from pymongo import UpdateOne

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

try:
    from db.mongo import MongoClientManager
except ModuleNotFoundError:
    from backend.db.mongo import MongoClientManager

TARGET_VALUE = "Thuế - Phí - Lệ Phí"
TARGET_DB = "legal_tax_chatbot"
TARGET_COLLECTION = "tax_fee_legal_sector_documents"
OUTPUT_PATH = Path("./data/tax_fee_legal_documents.json")
BATCH_SIZE = 1000


def main() -> None:
    mongo = MongoClientManager()
    mongo.ping()

    source_collection = mongo.get_collection("legal_documents")
    source_collection.create_index("metadata.legal_sectors")
    target_db = mongo.client[TARGET_DB]
    target_collection = target_db[TARGET_COLLECTION]
    target_collection.create_index("source_id", unique=True)
    target_collection.create_index("metadata.legal_sectors")

    query = {"metadata.legal_sectors": TARGET_VALUE}
    docs: list[dict] = []
    operations: list[UpdateOne] = []
    exported = 0
    scanned = 0

    cursor = source_collection.find(query, {"_id": 0}, no_cursor_timeout=True).batch_size(BATCH_SIZE)
    try:
        for doc in cursor:
            scanned += 1
            source_id = doc.get("source_id") or f"tax-fee-{scanned}"
            doc["source_id"] = source_id
            doc["target_bot"] = "tax-chatbot"
            docs.append(doc)

            operations.append(UpdateOne({"source_id": source_id}, {"$set": doc}, upsert=True))
            if len(operations) >= BATCH_SIZE:
                target_collection.bulk_write(operations, ordered=False)
                exported += len(operations)
                operations.clear()

        if operations:
            target_collection.bulk_write(operations, ordered=False)
            exported += len(operations)
            operations.clear()
    finally:
        cursor.close()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(docs, file, ensure_ascii=False, indent=2)

    print("source_match_count=", scanned)
    print("exported_to_target=", exported)
    print("target_db=", TARGET_DB)
    print("target_collection=", TARGET_COLLECTION)
    print("output_file=", str(OUTPUT_PATH.resolve()))

    mongo.close()


if __name__ == "__main__":
    main()
