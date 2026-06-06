import ast
import json
from pathlib import Path
from typing import Any, List
import redis
from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.core.interfaces.system.i_logging import ILogger


class RedisCacheService(ICacheService):
    def __init__(self, redis_client: redis.Redis, metadata_dir: Path, logger: ILogger):
        if not redis_client:
            raise ValueError("redis_client is required")
        self.redis_client = redis_client
        self.logger = logger

        self.metadata_dir = metadata_dir/ "cache"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline = self.redis_client.pipeline()

    def set(self, key: str, value: List[tuple[str, str]], expire: int | None = None, file_caller: str = ""):
        self.logger.info(f"Setting cache key: {key}", Path(__file__).name, file_caller, self.set.__name__)
        self.pipeline.set(key, str(value), ex=expire)
        self.pipeline.execute()
        self.logger.info(f"Cache key: {key} set", Path(__file__).name, file_caller, self.set.__name__)

    def get(self, key: str, file_caller: str = ""):
        self.logger.info(f"Getting cache key: {key}", Path(__file__).name, file_caller, self.get.__name__)
        result = self.redis_client.get(key)
        self.logger.info(f"Cache key: {key} retrieved with value: {result}", Path(__file__).name, file_caller, self.get.__name__)
        return self.__convert_to_origin_type(result)

    def delete(self, key: str, file_caller: str = ""):
        self.logger.info(f"Deleting cache key: {key}", Path(__file__).name, file_caller, self.delete.__name__)
        self.pipeline.delete(key)
        self.pipeline.execute()
        self.logger.info(f"Cache key: {key} deleted", Path(__file__).name, file_caller, self.delete.__name__)

    def clear(self, file_caller: str = ""):
        self.logger.info("Clearing all cache keys", Path(__file__).name, file_caller, self.clear.__name__)
        self.pipeline.flushall()
        self.pipeline.execute()
        self.logger.info("All cache keys cleared", Path(__file__).name, file_caller, self.clear.__name__)

    def exists(self, key: str, file_caller: str = ""):
        self.logger.info(f"Checking if cache key exists: {key}", Path(__file__).name, file_caller, self.exists.__name__)
        result = self.redis_client.exists(key)
        self.logger.info(f"Cache key: {key} exists: {result}", Path(__file__).name, file_caller, self.exists.__name__)
        return result
    
    def __convert_to_origin_type(self, value: Any):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
        
