import time


class CacheService:
    """In-memory cache placeholder.

    Replace with Redis in production.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, dict]] = {}
        self.default_ttl_seconds = 300

    def get(self, key: str) -> dict | None:
        data = self._store.get(key)
        if not data:
            return None
        expires_at, value = data
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: dict, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        self._store[key] = (time.time() + ttl, value)
