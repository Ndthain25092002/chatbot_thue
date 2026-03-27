from dataclasses import dataclass
import os


@dataclass
class Settings:
    app_name: str = "legal-chatbot"
    environment: str = os.getenv("ENVIRONMENT", "development")
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "legal_chatbot")
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss.index")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    generator_model: str = os.getenv("GENERATOR_MODEL", "gpt-4o-mini")


settings = Settings()
