import json
from pathlib import Path
import redis
from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService


class RedisCacheService(ICacheService):
    def __init__(self, redis_client: redis.Redis, logger, metadata_dir: Path):
        if not redis_client:
            raise ValueError("redis_client is required")
        self.redis_client = redis_client
        self.logger = logger

        self.metadata_dir = metadata_dir/ "cache"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline = self.redis_client.pipeline()

    def set(self, key: str, value, expire=None, file_caller=""):
        self.logger.info(f"Setting cache key: {key}", Path(__file__).name, file_caller)
        self.pipeline.set(key, value, ex=expire)
        self.pipeline.execute()
        self.logger.info(f"Cache key: {key} set", Path(__file__).name, file_caller)

    def get(self, key: str, file_caller=""):
        self.logger.info(f"Getting cache key: {key}", Path(__file__).name, file_caller)
        result = self.redis_client.get(key)
        self.logger.info(f"Cache key: {key} retrieved with value: {result}", Path(__file__).name, file_caller)
        return result

    def delete(self, key: str, file_caller=""):
        self.logger.info(f"Deleting cache key: {key}", Path(__file__).name, file_caller)
        self.pipeline.delete(key)
        self.pipeline.execute()
        self.logger.info(f"Cache key: {key} deleted", Path(__file__).name, file_caller)

    def clear(self, file_caller=""):
        self.logger.info("Clearing all cache keys", Path(__file__).name, file_caller)
        self.pipeline.flushall()
        self.pipeline.execute()
        self.logger.info("All cache keys cleared", Path(__file__).name, file_caller)

    def exists(self, key: str, file_caller=""):
        self.logger.info(f"Checking if cache key exists: {key}", Path(__file__).name, file_caller)
        result = self.redis_client.exists(key)
        self.logger.info(f"Cache key: {key} exists: {result}", Path(__file__).name, file_caller)
        return result
