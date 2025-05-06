import redis
import pickle
from logging import getLogger
import settings

logger = getLogger(__name__)
class RedisManager:
    def __init__(self, redis_url: str, max_connections: int = 10):
        self.pool = redis.ConnectionPool(host=redis_url, max_connections=max_connections)
        self.connection = redis.StrictRedis(connection_pool=self.pool)

    def set(self, key: str, value: str, expiration: int = 3600):
        try:
            if pickled := pickle.dumps(value):
                result = self.connection.setex(key, expiration, pickled)
                if not result:
                    raise ValueError('RedisCache could not set the value.')
            else:
                logger.error('pickle error, value={}', value)
        except TypeError as e:
            raise TypeError(f'Redis accepts values that can be pickled {e}')
        finally:
            self.close()

    def set_no_expiration(self, key: str, value: str):
        try:
            if pickled := pickle.dumps(value):
                result = self.connection.set(key, pickled)
                if not result:
                    raise ValueError('RedisCache could not set the value.')
            else:
                logger.error('pickle error, value={}', value)
        except TypeError as e:
            raise TypeError(f'Redis accepts values that can be pickled {e}')
        finally:
            self.close()
    
    def setNx(self, key: str, value: str, expiration: int = 3600):
        try:
            if pickled := pickle.dumps(value):
                result = self.connection.setnx(key, pickled)
                self.connection.expire(key, expiration)
                if not result:
                    return False
                return True
        except TypeError as e:
            raise TypeError(f'Redis accepts values that can be pickled {e}')
        finally:
            self.close()
    
    def hsetkey(self, name, key, value, expiration=3600):
        try:
            r = self.connection.hset(name, key, value)
            if expiration:
                self.connection.expire(name, expiration)
            return r
        finally:
            self.close()

    def hset(self, name, map: dict, expiration=3600):
        try:
            r = self.connection.hset(name, mapping=map)
            if expiration:
                self.connection.expire(name, expiration)
            return r
        finally:
            self.close()

    def hget(self, name, key):
        try:
            return self.connection.hget(name, key)
        finally:
            self.close()

    def get(self, key: str) -> str:
        try:
            pickled = self.connection.get(key)
            if pickled:
                return pickle.loads(pickled)
            else:
                return None
        finally:
            self.close()
    
    def delete(self, key: str):
        try:
            self.connection.delete(key)
        finally:
            self.close()
            
    def exists(self, key: str) -> bool:
        try:
            return self.connection.exists(key)
        finally:
            self.close()
            
    def close(self):
        self.connection.disconnect()


redis_client = RedisManager(settings.REDIS_URL)