import redis
from app.core.config import get_settings

settings = get_settings()

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True) 