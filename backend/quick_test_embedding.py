#!/usr/bin/env python3
"""Quick embedding test - just verify model loads and vector size."""

import sys
from rag.embedder import Embedder

try:
    print("Loading model...")
    emb = Embedder('intfloat/multilingual-e5-base')
    
    print("Testing query embedding...")
    q_vec = emb.embed_query("thue la gi")
    print(f"Query vector dim: {len(q_vec)}")
    
    print("Testing document embedding...")
    d_vecs = emb.embed_documents(["van ban phap luat"])
    print(f"Doc vector dim: {len(d_vecs[0]) if d_vecs else 0}")
    
    print("SUCCESS")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
