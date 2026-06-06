
from pathlib import Path

from backend.apps.core.interfaces.services.cache.i_connect_cache_session import IConnectCacheSession
import redis

from backend.apps.core.interfaces.services.cache.i_cache_service import ISingletonCache
from backend.apps.services.cache.radis_cache_service import RedisCacheService

class RedisCacheSession(IConnectCacheSession):
    def __init__(self, redis_client: redis.Redis, logger):
        self.redis_client = redis_client
        self.logger = logger

    def connect(self, file_caller="") -> ISingletonCache:
        self.logger.info("Connecting to Redis cache session...", Path(__file__).name, file_caller)
        return RedisCacheService(redis_client=self.redis_client, logger=self.logger)

    def disconnect(self, file_caller=""):
        self.logger.info("Disconnecting from Redis cache session...", Path(__file__).name, file_caller)
        self.redis_client.close()