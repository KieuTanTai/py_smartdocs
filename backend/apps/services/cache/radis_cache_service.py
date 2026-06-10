import ast
import datetime
import json
from pathlib import Path
from typing import Any, List
import numpy as np
import redis
from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.utils.path_file_helper import clear_all_files_on_path, create_path_file, delete_file_metadata_with_file_name


class RedisCacheService(ICacheService):
    def __init__(self, redis_client: redis.Redis, metadata_dir: Path, logger: ILogger):
        if not redis_client:
            raise ValueError("redis_client is required")
        self.redis_client = redis_client
        self.logger = logger

        self.metadata_dir = metadata_dir/ "cache"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline = self.redis_client.pipeline()

    def set(self, key: str, value: List[tuple[np.int64, str]], expire: int | None = None, file_caller: str = "") -> Path | None:
        self.logger.info(f"Setting cache key: {key}", Path(__file__).name, file_caller, self.set.__name__)
        self.pipeline.set(key, str(value), ex=expire)
        self.pipeline.execute()
        self.logger.info(f"Cache key: {key} set", Path(__file__).name, file_caller, self.set.__name__)
        return self.__write_metadata(key, str(value))


    def get(self, key: str, file_caller: str = "") -> List[Any] | None:
        self.logger.info(f"Getting cache key: {key}", Path(__file__).name, file_caller, self.get.__name__)
        result = self.redis_client.get(key)
        self.logger.info(f"Cache key: {key} retrieved with value: {result}", Path(__file__).name, file_caller, self.get.__name__)
        return self.__convert_to_origin_type(result)

    def delete(self, key: str, file_caller: str = "") -> int:
        self.logger.info(f"Deleting cache key: {key}", Path(__file__).name, file_caller, self.delete.__name__)
        self.pipeline.delete(key)
        self.pipeline.execute()
        self.logger.info(f"Cache key: {key} deleted", Path(__file__).name, file_caller, self.delete.__name__)
        return delete_file_metadata_with_file_name(self.metadata_dir, key, "json", self.logger)

    def clear(self, file_caller: str = "") -> int:
        self.logger.info("Clearing all cache keys", Path(__file__).name, file_caller, self.clear.__name__)
        self.pipeline.flushall()
        self.pipeline.execute()
        self.logger.info("All cache keys cleared", Path(__file__).name, file_caller, self.clear.__name__)
        return clear_all_files_on_path(self.metadata_dir, self.logger)

    def exists(self, key: str, file_caller: str = ""):
        self.logger.info(f"Checking if cache key exists: {key}", Path(__file__).name, file_caller, self.exists.__name__)
        result = self.redis_client.exists(key)
        self.logger.info(f"Cache key: {key} exists: {result}", Path(__file__).name, file_caller, self.exists.__name__)
        return result
    
    def __write_metadata(self, key: str, value: str):
        destination_path = create_path_file(self.metadata_dir, key, "json")
        with open(destination_path, "w") as f:
            json.dump(str(value), f)
        self.logger.info(f"Metadata for cache key: {key} written to {destination_path}", Path(__file__).name, Path(__file__).name, self.__write_metadata.__name__)

    def __convert_to_origin_type(self, value: Any):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
        
