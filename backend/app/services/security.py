from app.core.redis import redis_client
from datetime import timedelta
import re
import logging

logging.basicConfig(filename='auth_audit.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 15 * 60  # 15 minutes


def get_failed_attempts_key(email: str) -> str:
    return f"failed_attempts:{email}"

def get_lockout_key(email: str) -> str:
    return f"lockout:{email}"

def is_account_locked(email: str) -> bool:
    return redis_client.exists(get_lockout_key(email)) == 1

def increment_failed_attempts(email: str):
    key = get_failed_attempts_key(email)
    attempts = redis_client.incr(key)
    if attempts == 1:
        redis_client.expire(key, LOCKOUT_TIME_SECONDS)
    if attempts >= MAX_FAILED_ATTEMPTS:
        redis_client.set(get_lockout_key(email), 1, ex=LOCKOUT_TIME_SECONDS)
        redis_client.delete(key)
    return attempts

def reset_failed_attempts(email: str):
    redis_client.delete(get_failed_attempts_key(email))
    redis_client.delete(get_lockout_key(email))

def validate_password_complexity(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character.")

def log_auth_event(event_type: str, user: str, detail: str = ""):
    logging.info(f"{event_type} | user={user} | {detail}") 