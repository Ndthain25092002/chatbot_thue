from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, List

from data_pipeline.chunker import LegalDocumentChunker
from db.faiss_index import FaissIndex
from rag.embedder import Embedder
from rag.retriever import Retriever


def run_e2e_test() -> Dict[str, Any]:
    """Run end-to-end test: chunk -> embed -> index -> retrieve."""
    legal_text = """
NGHỊ QUYẾT
Số: 19/2023/NQ-HĐND
HỘI ĐỒNG NHÂN DÂN TỈNH ĐỒNG NAI
Đồng Nai, ngày 12 tháng 07 năm 2023

Căn cứ Luật Tổ chức chính quyền địa phương;
Xét đề nghị của Ủy ban nhân dân tỉnh Đồng Nai.

Điều 1. Phạm vi điều chỉnh
1. Nghị quyết này quy định chính sách hỗ trợ doanh nghiệp nhỏ và vừa trên địa bàn tỉnh Đồng Nai.
2. Chính sách áp dụng cho các doanh nghiệp đáp ứng điều kiện về lao động, doanh thu và nghĩa vụ thuế.

Điều 2. Đối tượng áp dụng
1. Doanh nghiệp nhỏ và vừa thành lập và hoạt động theo pháp luật Việt Nam.
2. Cơ quan nhà nước, tổ chức và cá nhân có liên quan đến việc triển khai chính sách hỗ trợ.

Điều 3. Hiệu lực thi hành
Nghị quyết này có hiệu lực từ ngày 01 tháng 09 năm 2023.
""".strip()

    chunker = LegalDocumentChunker()
    embedder = Embedder("intfloat/multilingual-e5-base")

    chunks = chunker.chunk_document(legal_text)
    if not chunks:
        raise RuntimeError("Chunking failed: no chunks returned")

    chunk_texts: List[str] = [item["content"] for item in chunks]
    chunk_metadata: List[Dict[str, Any]] = []
    for idx, item in enumerate(chunks):
        metadata = dict(item.get("metadata", {}))
        metadata.update(
            {
                "chunk_id": f"chunk-{idx+1}",
                "content": item["content"],
                "source": "e2e-sample-doc",
            }
        )
        chunk_metadata.append(metadata)

    vectors = embedder.embed_documents(chunk_texts)
    if not vectors:
        raise RuntimeError("Embedding failed: no vectors returned")

    with tempfile.TemporaryDirectory() as tmpdir:
        import db.faiss_index as faiss_module

        original_path = faiss_module.settings.faiss_index_path
        faiss_module.settings.faiss_index_path = str(Path(tmpdir) / "e2e_test.faiss")

        try:
            index = FaissIndex()
            index.add_documents(vectors, chunk_metadata)
            index.save()

            reloaded_index = FaissIndex()
            reloaded_index.load()

            query = "chính sách hỗ trợ doanh nghiệp nhỏ và vừa"
            query_vec = embedder.embed_query(query)
            results = reloaded_index.search(query_vec, top_k=3)

            retriever = Retriever()
            retriever.index = reloaded_index
            retriever_results = retriever.retrieve(query_vec, top_k=3)

            return {
                "chunks": len(chunks),
                "vector_dim": len(vectors[0]),
                "index_size": reloaded_index.get_size(),
                "query": query,
                "results": results,
                "retriever_results": retriever_results,
            }
        finally:
            faiss_module.settings.faiss_index_path = original_path


def main() -> None:
    output = run_e2e_test()
    print("E2E test completed")
    print(f"chunks={output['chunks']}")
    print(f"vector_dim={output['vector_dim']}")
    print(f"index_size={output['index_size']}")
    print(f"query={output['query']}")

    for idx, item in enumerate(output["results"], start=1):
        title = item.get("title", "")
        article = item.get("article", "")
        score = item.get("score", 0.0)
        print(f"result_{idx}=title:{title}|article:{article}|score:{score:.4f}")

    print(f"retriever_result_count={len(output['retriever_results'])}")


if __name__ == "__main__":
    main()
