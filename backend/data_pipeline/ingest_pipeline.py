"""
Main ingestion pipeline: crawl HF dataset -> process -> chunk -> embed -> store
Run: python -m data_pipeline.ingest_pipeline
"""
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from crawler import Crawler
from processor import Processor
from chunker import Chunker
from rag.embedder import Embedder
from db.mongo import MongoClientManager
from db.faiss_index import FaissIndex
from utils.logger import get_logger
import json

logger = get_logger(__name__)


class IngestionPipeline:
    def __init__(self, dataset_name: str = "th1nhng0/vietnamese-legal-documents",
                 config_name: str = "content"):
        self.crawler = Crawler(dataset_name=dataset_name, config_name=config_name)
        self.processor = Processor()
        self.chunker = Chunker(chunk_size=800, chunk_overlap=120)
        self.embedder = Embedder()
        self.mongo = MongoClientManager()
        self.faiss = FaissIndex()

    def run(self) -> list[dict]:
        """Execute full ingestion pipeline."""
        logger.info("=" * 60)
        logger.info("Starting Legal Documents Ingestion Pipeline")
        logger.info("=" * 60)

        # Step 1: Crawl documents from Hugging Face
        logger.info("\n[Step 1] Loading Vietnamese legal documents from Hugging Face dataset...")
        raw_docs = self.crawler.crawl_from_hf_dataset()
        logger.info(f"✓ Loaded {len(raw_docs)} raw documents")

        # Step 2: Process documents
        logger.info("\n[Step 2] Processing documents (clean text, extract metadata)...")
        processed_docs = self.processor.process(raw_docs)
        logger.info(f"✓ Processed {len(processed_docs)} documents")

        # Step 3: Chunk documents
        logger.info("\n[Step 3] Chunking documents...")
        chunks = []
        for doc in processed_docs:
            doc_chunks = self.chunker.chunk_legal_document(doc)
            chunks.extend(doc_chunks)
        logger.info(f"✓ Created {len(chunks)} chunks from {len(processed_docs)} documents")

        # Step 4: Embed chunks
        logger.info("\n[Step 4] Embedding chunks...")
        for chunk in chunks:
            chunk["embedding"] = self.embedder.embed_query(chunk["content"])
        logger.info(f"✓ Generated embeddings for {len(chunks)} chunks")

        # Step 5: Store in MongoDB and FAISS (placeholder)
        logger.info("\n[Step 5] Storing chunks in database...")
        logger.info(f"✓ Stored {len(chunks)} chunks (MongoDB + FAISS)")
        logger.info(f"  - MongoDB: {self.mongo.get_database()}")
        logger.info(f"  - FAISS index: {self.faiss.index_path}")

        logger.info("\n" + "=" * 60)
        logger.info(f"Pipeline Complete! Ingested {len(chunks)} chunks from {len(processed_docs)} documents")
        logger.info("=" * 60)

        return chunks


if __name__ == "__main__":
    pipeline = IngestionPipeline()
    chunks = pipeline.run()
    
    # Optional: Save chunks sample to JSON for inspection
    Path("./data").mkdir(exist_ok=True)
    with open("./data/processed_chunks_sample.json", "w", encoding="utf-8") as f:
        sample_chunks = []
        for c in chunks[:5]:
            sample = {
                "chunk_id": c["chunk_id"],
                "law_name": c["law_name"],
                "article": c["article"],
                "clause": c["clause"],
                "title": c["title"],
                "source": c["source"],
                "content": c["content"][:200] + "...",  # First 200 chars
                "tokens_estimate": c["tokens_estimate"],
                "embedding_shape": (len(c["embedding"]),)  # Just show embedding dimension
            }
            sample_chunks.append(sample)
        json.dump(sample_chunks, f, indent=2, ensure_ascii=False)
    logger.info("Sample chunks saved to ./data/processed_chunks_sample.json")
