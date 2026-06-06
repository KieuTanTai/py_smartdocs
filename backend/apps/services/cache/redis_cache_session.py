
from pathlib import Path

from backend.apps.core.interfaces.services.cache.i_connect_cache_session import IConnectCacheSession
import redis

from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.services.cache.radis_cache_service import RedisCacheService

class RedisCacheSession(IConnectCacheSession):
    def __init__(self, redis_client: redis.Redis, metadata_dir: Path, logger):
        self.redis_client = redis_client
        self.metadata_dir = metadata_dir
        self.logger = logger

    def connect(self, file_caller="") -> ICacheService:
        self.logger.info("Connecting to Redis cache session...", Path(__file__).name, file_caller, self.connect.__name__)
        return RedisCacheService(redis_client=self.redis_client, metadata_dir=self.metadata_dir, logger=self.logger)

    def disconnect(self, file_caller=""):
        self.logger.info("Disconnecting from Redis cache session...", Path(__file__).name, file_caller, self.disconnect.__name__)
        self.redis_client.close()