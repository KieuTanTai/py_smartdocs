
from pathlib import Path

from backend.apps.core.interfaces.services.cache.i_connect_cache_session import IConnectCacheSession
import redis

from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.services.cache.radis_cache_service import RedisCacheService

class RedisCacheSession(IConnectCacheSession):
    def __init__(self, config_provider: IConfigProvider, metadata_dir: Path, logger):
        if config_provider is None:
            raise ValueError("Redis configuration must be provided")
        self.redis_client = self.__create_redis_client(config_provider)
        self.metadata_dir = metadata_dir
        self.logger = logger

    def connect(self, file_caller="") -> ICacheService:
        self.logger.info("Connecting to Redis cache session...", Path(__file__).name, file_caller, self.connect.__name__)
        return RedisCacheService(redis_client=self.redis_client, metadata_dir=self.metadata_dir, logger=self.logger)

    def disconnect(self, file_caller=""):
        self.logger.info("Disconnecting from Redis cache session...", Path(__file__).name, file_caller, self.disconnect.__name__)
        self.redis_client.close()

    def __create_redis_client(self, config_provider: IConfigProvider) -> redis.Redis:
        config = config_provider.get_redis_config()
        host = config.get("host")
        if host is None:
            raise ValueError("Redis host must be provided in the configuration")
        port = config.get("port")
        if port is None:
            raise ValueError("Redis port must be provided in the configuration")
        db = config.get("db")
        if db is None:
            raise ValueError("Redis db must be provided in the configuration")
        return redis.Redis(host, port, db, decode_responses=True)