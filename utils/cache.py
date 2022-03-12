import time


class Item:
    def __init__(self, key, value, ttl=3600):
        self.expire_time = time.time() + ttl
        self.key = key
        self.value = value

    def expired(self):
        if time.time() > self.expire_time:
            return True
        else:
            return False


class Cache:
    cache_store = {}

    @classmethod
    def add(cls, key, value, ttl=3600):
        cls.cache_store[key] = Item(key, value, ttl)

    @classmethod
    def get(cls, key):
        if key not in cls.cache_store:
            return None
        v = cls.cache_store[key]
        if v.expired():
            del cls.cache_store[key]
            return None
        return v.value

