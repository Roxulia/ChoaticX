import redis
import json
import hashlib

class Cache:
    _client = None

    @classmethod
    def init(cls, host="127.0.0.1", port=6379, db=0):
        if cls._client is None:
            cls._client = redis.Redis(host=host, port=port, db=db)

    @classmethod
    def get(cls, key):
        data = cls._client.get(key)
        return json.loads(data) if data else None

    @classmethod
    def set(cls, key, value, ttl=60):  # ttl in seconds
        cls._client.setex(key, ttl, json.dumps(value, default=str))
