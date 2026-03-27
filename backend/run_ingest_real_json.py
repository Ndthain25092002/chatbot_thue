from pathlib import Path

from data_pipeline.ingest_pipeline import ingest_json_to_faiss

result = ingest_json_to_faiss(
    json_path=Path("data/tax_fee_legal_documents.json"),
    batch_size=8,
    max_records=50,
    clear_index=True,
)

print(result)
