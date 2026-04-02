from __future__ import annotations

import argparse
from pathlib import Path

from data_pipeline.ingest_pipeline import ingest_json_to_faiss
from db.faiss_index import FaissIndex
from services.legal_service import LegalService


def ensure_index(data_path: Path, max_records: int, batch_size: int) -> int:
    index = FaissIndex()
    current_size = index.get_size()
    if current_size > 0:
        print(f"FAISS index da co san: {current_size} vectors")
        return current_size

    if not data_path.exists():
        raise FileNotFoundError(f"Khong tim thay du lieu: {data_path}")

    print("FAISS index dang rong. Bat dau ingest du lieu mau...")
    result = ingest_json_to_faiss(
        json_path=data_path,
        batch_size=batch_size,
        max_records=max_records,
        clear_index=True,
    )
    print(
        "Ingest xong: "
        f"indexed_records={result['indexed_records']}, "
        f"faiss_size={result['faiss_size']}"
    )
    return result["faiss_size"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo chat terminal khong can BE/FE")
    parser.add_argument(
        "--data-path",
        default="data/tax_fee_legal_documents.json",
        help="Duong dan toi file JSON du lieu phap ly",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=80,
        help="So ban ghi toi da de ingest khi index rong (0 = toan bo)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size cho embedding khi ingest",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Khong auto ingest khi index rong",
    )
    args = parser.parse_args()

    data_path = Path(args.data_path)
    index = FaissIndex()
    if index.get_size() == 0:
        if args.skip_ingest:
            raise RuntimeError(
                "FAISS index dang rong va --skip-ingest duoc bat. "
                "Hay ingest truoc hoac bo --skip-ingest."
            )
        ensure_index(data_path, args.max_records, args.batch_size)
    else:
        print(f"San sang chat voi index size={index.get_size()}")

    service = LegalService()
    session_id = "terminal-demo"

    print("\n=== Legal Chat Terminal Demo ===")
    print("Nhap cau hoi va nhan Enter.")
    print("Go /exit de thoat.\n")

    while True:
        user_query = input("Ban> ").strip()
        if not user_query:
            continue
        if user_query.lower() in {"/exit", "exit", "quit", "/quit"}:
            print("Tam biet")
            break

        result = service.answer_question(user_query=user_query, session_id=session_id)

        print("\nBot>")
        print(result.get("answer", ""))
        print(f"\nconfidence={result.get('confidence', 0.0)}")

        sources = result.get("sources") or []
        if sources:
            print("nguon tham khao:")
            for idx, src in enumerate(sources[:3], start=1):
                title = src.get("title") or "(khong co tieu de)"
                score = src.get("score") or 0.0
                chunk_id = src.get("chunk_id") or ""
                print(f"  {idx}. {title} | chunk_id={chunk_id} | score={score:.4f}")
        print("")


if __name__ == "__main__":
    main()