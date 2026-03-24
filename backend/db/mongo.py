from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

try:
    from config import settings
except ModuleNotFoundError:
    from backend.config import settings


class MongoClientManager:
    """Provide MongoDB client, database and collection accessors."""

    def __init__(self) -> None:
        self.uri = settings.mongo_uri
        self.db_name = settings.mongo_db_name
        self._client: MongoClient | None = None

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            self._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
        return self._client

    def ping(self) -> bool:
        self.client.admin.command("ping")
        return True

    def get_database(self) -> Database:
        return self.client[self.db_name]

    def get_collection(self, collection_name: str) -> Collection:
        return self.get_database()[collection_name]

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
