import redis
import pickle
import json
from threading import Lock
import logging
from utils.SystemConfig import config

logger = logging.getLogger(__name__)

class RedisService:
    _instance = None
    _lock = Lock()
    CHAT_TWIN = "CHAT_TWIN"

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RedisService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        with self._lock:
            if hasattr(self, '_initialized'):
                return
            try:
                self.client =redis.Redis(
                    host=config.connection.redis_host,
                    port=config.connection.redis_port,                 # Cloud Run entry point is always 443
                    password=config.redis_password,
                    ssl=True,                 # This is mandatory for Cloud Run URLs
                    ssl_cert_reqs=None,       # Required because Cloud Run certs are managed
                    decode_responses=False
                )

                # self.client = redis.Redis(
                #     host=config.connection.redis_host,
                #     port=config.connection.redis_port,
                #     password=config.redis_password,
                #     decode_responses=False # We need bytes for pickle, but we can decode for JSON if needed
                # )
                self.client.ping()
                logger.info(f"Connected to Redis at {config.connection.redis_host}:{config.connection.redis_port}")
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    def set(self, key: str, value: any, expire: int = None):
        """
        Stores any type of value in Redis by pickling it.
        """
        try:
            pickled_value = pickle.dumps(value)
            self.client.set(key, pickled_value, ex=expire)
        except Exception as e:
            logger.error(f"Error storing key {key} in Redis: {e}")

    def get(self, key: str):
        """
        Retrieves a value from Redis and unpickles it.
        """
        try:
            value = self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error retrieving key {key} from Redis: {e}")
            return None

    def set_message_history(self, key: str, messages: list, expire: int = None):
        """
        Stores message history in Redis using JSON.
        """
        try:
            json_value = json.dumps(messages)
            self.client.set(key, json_value, ex=expire)
        except Exception as e:
            logger.error(f"Error storing message history for key {key} in Redis: {e}")

    def get_message_history(self, key: str):
        """
        Retrieves message history from Redis and parses JSON.
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Error retrieving message history for key {key} from Redis: {e}")
            return None

    def delete(self, key: str):
        """
        Deletes a key from Redis.
        """
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
