from dataclasses import dataclass
import os


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass
class Settings:
    app_name: str = "legal-chatbot"
    environment: str = os.getenv("ENVIRONMENT", "development")
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "legal_chatbot")
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss.index")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
    generator_model: str = os.getenv("GENERATOR_MODEL", "qwen2:7b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    generator_timeout_sec: float = _get_float("GENERATOR_TIMEOUT_SEC", 240.0)
    generator_temperature: float = _get_float("GENERATOR_TEMPERATURE", 0.2)
    generator_max_contexts: int = _get_int("GENERATOR_MAX_CONTEXTS", 5)


settings = Settings()
