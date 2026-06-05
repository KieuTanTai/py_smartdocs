
from backend.apps.core.interfaces.services.cache.i_connect_cache_session import IConnectCacheSession
import redis

class RedisCacheSession(IConnectCacheSession):
    def __init__(self, redis_client: redis.Redis, logger):
        self.redis_client = redis_client
        self.logger = logger

    def connect(self):
        self.logger.info("Connecting to Redis cache session...")
        return self.redis_client

    def disconnect(self):
        self.logger.info("Disconnecting from Redis cache session...")
        self.redis_client.close()