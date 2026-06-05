from pathlib import Path
import redis
from backend.apps.core.interfaces.services.cache.i_singleton_cache import ISingletonCache


class RedisCacheService(ISingletonCache):
    def __init__(self, redis_client: redis.Redis, logger):
        self.redis_client = redis_client
        self.logger = logger

    def set(self, key: str, value, expire=None, file_caller=""):
        self.logger.info(f"Setting cache key: {key}", Path(__file__).name, file_caller)
        self.redis_client.set(key, value, ex=expire)
        self.logger.info(f"Cache key: {key} set", Path(__file__).name, file_caller)

    def get(self, key: str, file_caller=""):
        self.logger.info(f"Getting cache key: {key}", Path(__file__).name, file_caller)
        result = self.redis_client.get(key)
        self.logger.info(f"Cache key: {key} retrieved with value: {result}", Path(__file__).name, file_caller)
        return result

    def delete(self, key: str, file_caller=""):
        self.logger.info(f"Deleting cache key: {key}", Path(__file__).name, file_caller)
        self.redis_client.delete(key)
        self.logger.info(f"Cache key: {key} deleted", Path(__file__).name, file_caller)

    def clear(self, file_caller=""):
        self.logger.info("Clearing all cache keys", Path(__file__).name, file_caller)
        self.redis_client.flushall()
        self.logger.info("All cache keys cleared", Path(__file__).name, file_caller)

    def exists(self, key: str, file_caller=""):
        self.logger.info(f"Checking if cache key exists: {key}", Path(__file__).name, file_caller)
        result = self.redis_client.exists(key)
        self.logger.info(f"Cache key: {key} exists: {result}", Path(__file__).name, file_caller)
        return result
