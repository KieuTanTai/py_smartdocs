import ast
from pathlib import Path

import numpy as np
import redis
from backend.apps.core.interfaces.services.cache.i_cache_param_value import ICacheParam, ICacheParamValue
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
    cache_param_value = ICacheParamValue(index=np.int64(1), text_value="test_value")
    second_cache_param_value = ICacheParamValue(index=np.int64(2), text_value="test_value_2")
    third_cache_param_value = ICacheParamValue(index=np.int64(3), text_value="test_value_3")
    input = ICacheParam(key="test_key", values=[cache_param_value, second_cache_param_value, third_cache_param_value])
    cache_service.set(input, file_caller=Path(__file__).name)
    result = cache_service.get("test_key", file_caller=Path(__file__).name)
    print("Result:", result)
    cache_service.set(ICacheParam(key="test_key_expire", values=[cache_param_value], expire=1), file_caller=Path(__file__).name)  # Set with expiration
    response1 = cache_service.get("test_key", file_caller=Path(__file__).name)
    response2 = cache_service.get("test_key_expire", file_caller=Path(__file__).name)
    print("Response 1:", type(response1), response1)
    print("Response 2:", type(response2), response2)
    response3 = cache_service.exists("test_key", file_caller=Path(__file__).name)
    print("Response 3:", type(response3) == int, response3)
    # cache_service.delete("test_key", file_caller=Path(__file__).name)
    # cache_service.delete("test_key_expire", file_caller=Path(__file__).name)
    # cache_service.clear(file_caller=Path(__file__).name)
    if response1 is not None:
        print("index in first response:", [value.index for value in response1.values])
        print("value in first response:", [value.text_value for value in response1.values])
    cache_client.disconnect(file_caller=Path(__file__).name)

if __name__ == "__main__":
    test_redis_cache()
    print("All tests passed!")
