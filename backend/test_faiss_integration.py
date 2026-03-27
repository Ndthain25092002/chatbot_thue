#!/usr/bin/env python3
"""Test FAISS index with real embeddings from multilingual-e5-base."""

import json
import tempfile
from pathlib import Path

from rag.embedder import Embedder
from db.faiss_index import FaissIndex


def test_faiss_integration():
    """End-to-end test: embed documents, add to FAISS, search, save/load."""
    
    # Sample legal documents
    documents = [
        {
            "chunk_id": "doc-001-art-1",
            "content": "Điều 1. Phạm vi điều chỉnh\n1. Luật này điều chỉnh các hoạt động về thuế thu nhập cá nhân",
            "doc_type": "LUẬT",
            "title": "Phạm vi điều chỉnh"
        },
        {
            "chunk_id": "doc-001-art-2",
            "content": "Điều 2. Đối tượng nộp thuế\n1. Cá nhân cư trú tại Việt Nam nộp thuế toàn bộ thu nhập",
            "doc_type": "LUẬT",
            "title": "Đối tượng nộp thuế"
        },
        {
            "chunk_id": "doc-002-art-1",
            "content": "Quyết định 100/QĐ-TTg về chính sách hỗ trợ doanh nghiệp nhỏ và vừa",
            "doc_type": "QUYẾT ĐỊNH",
            "title": "Chính sách hỗ trợ doanh nghiệp"
        },
    ]
    
    # Create embedder and embed documents
    print("Creating embedder...")
    embedder = Embedder('intfloat/multilingual-e5-base')
    
    print(f"Embedding {len(documents)} documents...")
    doc_texts = [doc['content'] for doc in documents]
    embeddings = embedder.embed_documents(doc_texts)
    print(f"✓ Generated {len(embeddings)} embeddings, each with dimension {len(embeddings[0])}")
    
    # Create temp FAISS index for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_index_path = Path(tmpdir) / "test_index.faiss"
        
        # Patch config for testing
        import db.faiss_index
        original_path = db.faiss_index.settings.faiss_index_path
        db.faiss_index.settings.faiss_index_path = str(test_index_path)
        
        try:
            # Create index and add documents
            print("\nAdding documents to FAISS index...")
            index = FaissIndex()
            index.add_documents(embeddings, documents)
            print(f"✓ Index size: {index.get_size()} vectors")
            
            # Save index
            print("Saving index to disk...")
            index.save()
            print(f"✓ Saved to {test_index_path}")
            
            # Load fresh index from disk
            print("Loading index from disk...")
            index2 = FaissIndex()
            index2.load()
            print(f"✓ Loaded {index2.get_size()} vectors")
            
            # Test search with a query
            print("\nTesting search...")
            query_text = "chính sách hỗ trợ doanh nghiệp nhỏ"
            query_embedding = embedder.embed_query(query_text)
            print(f"Query: '{query_text}'")
            
            results = index2.search(query_embedding, top_k=2)
            print(f"✓ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.get('title', 'N/A')} (score: {result.get('score', 0):.4f})")
                print(f"     Type: {result.get('doc_type', 'N/A')} | ID: {result.get('chunk_id', 'N/A')}")
            
            print("\n✓ FAISS integration test completed successfully!")
            return True
            
        finally:
            # Restore original config
            db.faiss_index.settings.faiss_index_path = original_path


if __name__ == "__main__":
    test_faiss_integration()
