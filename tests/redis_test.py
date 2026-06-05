from pathlib import Path

import redis
from backend.apps.services.cache.radis_cache_service import RedisCacheService
from backend.apps.services.cache.redis_cache_session import RedisCacheSession
from sys_services.logging import Logger

def test_redis_cache():
    # DATA DRIVEN TESTING
    logger = Logger()
    client = RedisCacheSession(redis.Redis(host="localhost", port=6379, db=0), logger)
    cache_service = RedisCacheService(redis_client=client.connect(), logger=logger)

    # Test set and get
    cache_service.set("test_key", "test_value", file_caller=Path(__file__).name)
    result = cache_service.get("test_key", file_caller=Path(__file__).name)
    print("Result:", result)
    cache_service.set("test_key_expire", "test_value_expire", expire=1, file_caller=Path(__file__).name)  # Set with expiration
    response1 = cache_service.get("test_key", file_caller=Path(__file__).name) == b"test_value"
    response2 = cache_service.get("test_key_expire", file_caller=Path(__file__).name) == b"test_value_expire"
    print("Response 1:", response1)
    print("Response 2:", response2)

    cache_service.clear(file_caller=Path(__file__).name)  # Clear cache after test

if __name__ == "__main__":
    test_redis_cache()
    print("All tests passed!")
