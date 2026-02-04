import redis
from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB

def get_cache():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def test_cache():
    r = get_cache()
    r.set('key_test', 'value_test', ex=15)

test_cache()