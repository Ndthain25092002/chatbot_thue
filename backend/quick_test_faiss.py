#!/usr/bin/env python3
"""Quick FAISS test - minimal output."""

import tempfile
from pathlib import Path

from rag.embedder import Embedder
from db.faiss_index import FaissIndex


docs = [
    {
        "chunk_id": "doc-001-art-1",
        "content": "Điều 1. Phạm vi điều chỉnh - Luật này điều chỉnh các hoạt động về thuế",
        "doc_type": "LUẬT",
        "title": "Phạm vi điều chỉnh"
    },
    {
        "chunk_id": "doc-001-art-2",
        "content": "Điều 2. Đối tượng nộp thuế - Cá nhân nộp thuế toàn bộ thu nhập",
        "doc_type": "LUẬT",
        "title": "Đối tượng nộp thuế"
    },
    {
        "chunk_id": "doc-002-art-1",
        "content": "Quyết định 100/QĐ-TTg về hỗ trợ doanh nghiệp nhỏ và vừa",
        "doc_type": "QUYẾT ĐỊNH",
        "title": "Chính sách hỗ trợ doanh nghiệp"
    },
]

print("1. Creating embedder...")
emb = Embedder('intfloat/multilingual-e5-base')

print("2. Embedding documents...")
doc_texts = [d['content'] for d in docs]
embeddings = emb.embed_documents(doc_texts)
print(f"   ✓ {len(embeddings)} embeddings created")

# Test with tmp dir
with tempfile.TemporaryDirectory() as tmpdir:
    import db.faiss_index
    old_path = db.faiss_index.settings.faiss_index_path
    db.faiss_index.settings.faiss_index_path = str(Path(tmpdir) / "test.faiss")
    
    try:
        print("3. Adding to FAISS index...")
        idx = FaissIndex()
        idx.add_documents(embeddings, docs)
        print(f"   ✓ Index size: {idx.get_size()}")
        
        print("4. Saving index...")
        idx.save()
        print(f"   ✓ Saved")
        
        print("5. Loading index...")
        idx2 = FaissIndex()
        idx2.load()
        print(f"   ✓ Loaded: {idx2.get_size()} vectors")
        
        print("6. Searching...")
        query_vec = emb.embed_query("thue va chinh sach ho tro")
        results = idx2.search(query_vec, top_k=2)
        print(f"   ✓ Found {len(results)} results:")
        for r in results:
            print(f"     - {r.get('title')} (score: {r.get('score'):.4f})")
        
        print("\n✓ FAISS test SUCCESS!")
    finally:
        db.faiss_index.settings.faiss_index_path = old_path
