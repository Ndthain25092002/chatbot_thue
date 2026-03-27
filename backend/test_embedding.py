#!/usr/bin/env python3
"""Test embedding with multilingual-e5-base model."""

from rag.embedder import Embedder

# Initialize embedder
print("Initializing Embedder with intfloat/multilingual-e5-base...")
print("This may take a moment on first run (downloading ~1.1GB model)...\n")
emb = Embedder('intfloat/multilingual-e5-base')

# Test query embedding
query_text = "thue thu nhap ca nhan la gi"
print(f"Embedding query: '{query_text}'")
query_vector = emb.embed_query(query_text)
print(f"✓ Query vector size: {len(query_vector)}")
print(f"  First 5 values: {query_vector[:5]}")

# Test document embedding
doc_texts = [
    "Noi dung van ban phap luat ve thue thu nhap ca nhan",
    "Dieu 1. Pham vi dieu chinh cua luat thue",
    "Khoang 1. Dieu chinh doi tuong nhan thue",
]
print(f"\nEmbedding {len(doc_texts)} documents...")
doc_vectors = emb.embed_documents(doc_texts)
print(f"✓ Number of document vectors: {len(doc_vectors)}")
print(f"✓ Size of each vector: {len(doc_vectors[0]) if doc_vectors else 0}")
print(f"  First doc vector (first 5 values): {doc_vectors[0][:5] if doc_vectors else []}")

# Verify vector dimensions match
if len(query_vector) == len(doc_vectors[0]):
    print(f"\n✓ SUCCESS! Query and document vectors have matching dimension: {len(query_vector)}")
else:
    print(f"\n✗ ERROR! Dimension mismatch: query {len(query_vector)} vs doc {len(doc_vectors[0])}")

# Test similarity computation (dot product)
if query_vector and doc_vectors:
    import numpy as np
    q_array = np.array(query_vector)
    d_array = np.array(doc_vectors[0])
    similarity = np.dot(q_array, d_array)
    print(f"✓ Sample cosine similarity (query vs first doc): {similarity:.4f}")

print("\n✓ Embedding test completed successfully!")
