import ast
import datetime
import json
from pathlib import Path
from typing import Any, List
import numpy as np
import redis
from backend.apps.core.interfaces.services.cache.i_cache_param_value import ICacheParam, ICacheParamValue
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

    def set(self, input: ICacheParam, file_caller: str = "") -> Path | None:
        self.logger.info(f"Setting cache key: {input.key}", Path(__file__).name, file_caller, self.set.__name__)
        value_str = self.__convert_to_serializable(input.key, input.values, input.expire)
        self.pipeline.set(input.key, value_str, ex=input.expire)
        self.pipeline.execute()
        self.logger.info(f"Cache key: {input.key} set", Path(__file__).name, file_caller, self.set.__name__)
        return self.__write_metadata(input.key, value_str)


    def get(self, key: str, file_caller: str = "") -> ICacheParam | None:
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
    
    def __write_metadata(self, key: str, input_value: str) -> Path | None:
        destination_path = create_path_file(self.metadata_dir, key, "json")
        try: 
            input_value_json = json.loads(input_value)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding cache value for metadata: {e}", Path(__file__).name, Path(__file__).name, self.__write_metadata.__name__)
            return None
        with open(destination_path, "w") as f:
            json.dump(input_value_json, f, ensure_ascii=False, indent=4)
        self.logger.info(f"Metadata for cache key: {key} written to '{destination_path}'", Path(__file__).name, Path(__file__).name, self.__write_metadata.__name__)
        return destination_path

    def __convert_to_serializable(self, value_key: str, value: List[ICacheParamValue], expire: int | None = None) -> str:
        return json.dumps({"key": value_key, "value": self.__normalize_value(value), "expire": expire})
    
    def __normalize_value(self, values: List[ICacheParamValue]):
        result = [
            {"index": int(value.index), "text_value": value.text_value} for value in values
        ]
        return result

    def __convert_to_origin_type(self, value: Any) -> ICacheParam | None:
        try:
            loads = json.loads(value) if value else None
            if loads is None:
                return None
            return ICacheParam(
                key=loads["key"],
                values=[ICacheParamValue(index=np.int64(item["index"]), text_value=item["text_value"]) for item in loads["value"]]
            )
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding cache value: {e}", Path(__file__).name, Path(__file__).name, self.__convert_to_origin_type.__name__)
            return None
        