import json
from redis.asyncio import Redis

# Global Redis client
redis_client: Redis | None = None


# 🔥 Initialize Redis connection
async def init_redis():
    global redis_client

    try:
        redis_client = Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        # Test connection
        await redis_client.ping()
        print("✅ Redis connected")

    except Exception as e:
        redis_client = None
        print(f"⚠️ Redis unavailable, using in-memory fallback: {e}")


# 🔥 Get client
def get_redis():
    return redis_client


async def is_rate_limited(user_id: int, limit: int = 10, window_seconds: int = 60):
    if not redis_client:
        return False

    try:
        key = f"rate:{user_id}"
        request_count = await redis_client.incr(key)

        if request_count == 1:
            await redis_client.expire(key, window_seconds)

        return request_count > limit
    except Exception:
        return False


# 🔥 Idempotency cache
async def get_cached_transaction(transaction_id: str):
    if redis_client:
        data = await redis_client.get(f"txn:{transaction_id}")
        if data:
            return json.loads(data)
    return None


async def set_cached_transaction(transaction_id: str, value: dict):
    if redis_client:
        await redis_client.set(
            f"txn:{transaction_id}",
            json.dumps(value),
            ex=600  # TTL = 10 min
        )


# 🔥 User profile cache (feature store)
async def get_user_profile(user_id: int):
    if redis_client:
        data = await redis_client.get(f"user:{user_id}")
        if data:
            return json.loads(data)
    return None


async def set_user_profile(user_id: int, profile: dict):
    if redis_client:
        await redis_client.set(
            f"user:{user_id}",
            json.dumps(profile)
        )
