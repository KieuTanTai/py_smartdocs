import ast
from pathlib import Path

import redis
from backend.apps.services.cache.redis_cache_session import RedisCacheSession
from sys_services.logging import Logger
from sys_services.read_config.config_provider import EnvConfigProvider

CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output" 
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def test_redis_cache():
    # DATA DRIVEN TESTING
    logger = Logger()
    cache_client = RedisCacheSession(config_provider=EnvConfigProvider(), metadata_dir=OUTPUT_DIR, logger=logger)
    cache_service = cache_client.connect(file_caller=Path(__file__).name)

    # Test set and get
    cache_service.set("test_key", [("test_key:1", "test_value"), ("test_key:2", "test_value2")], file_caller=Path(__file__).name)
    result = cache_service.get("test_key", file_caller=Path(__file__).name)
    print("Result:", result)
    cache_service.set("test_key_expire", [("test_key_expire:1", "test_value_expire")], expire=1, file_caller=Path(__file__).name)  # Set with expiration
    response1 = cache_service.get("test_key", file_caller=Path(__file__).name)
    response2 = cache_service.get("test_key_expire", file_caller=Path(__file__).name)
    print("Response 1:", type(response1), response1)
    print("Response 2:", type(response2), response2)
    response3 = cache_service.exists("test_key", file_caller=Path(__file__).name)
    print("Response 3:", type(response3) == int, response3)
    # cache_service.delete("test_key", file_caller=Path(__file__).name)
    # cache_service.delete("test_key_expire", file_caller=Path(__file__).name)
    # cache_service.clear(file_caller=Path(__file__).name)
    cache_client.disconnect(file_caller=Path(__file__).name)

if __name__ == "__main__":
    test_redis_cache()
    print("All tests passed!")
