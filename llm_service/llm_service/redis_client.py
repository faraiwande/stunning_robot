import os
import redis
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

def get_user_state(phone):
    data = r.get(f"user:{phone}")
    return json.loads(data) if data else {}

def set_user_state(phone, state):
    r.set(f"user:{phone}", json.dumps(state), ex=3600)

def clear_user_state(phone):
    r.delete(f"user:{phone}")

# 📜 Conversation History
def add_to_history(phone, sender, text):
    entry = json.dumps({"from": sender, "text": text})
    r.rpush(f"history:{phone}", entry)
    r.ltrim(f"history:{phone}", -30, -1)  # Keep only last 30 messages

def get_history(phone):
    raw = r.lrange(f"history:{phone}", 0, -1)
    return [json.loads(h) for h in raw]
