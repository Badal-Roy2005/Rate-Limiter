import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

LIMIT = 5
WINDOW = 60

redis_client = None


@app.on_event("startup")
def connect_to_redis():
    global redis_client
    try:
        redis_client = redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
        )
        redis_client.ping()
        print("Connected to Redis.")
    except Exception as exc:
        redis_client = None
        print(f"Warning: could not connect to Redis: {exc}")


CHECK_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('GET', key)

if current == false then
    redis.call('SET', key, 1)
    redis.call('EXPIRE', key, window)
    local ttl = redis.call('TTL', key)
    return {1, limit - 1, ttl, 1}
end

local count = tonumber(current)

if count >= limit then
    local ttl = redis.call('TTL', key)
    return {count, 0, ttl, 0}
end

redis.call('INCR', key)
local new_count = tonumber(redis.call('GET', key))
local ttl = redis.call('TTL', key)
return {new_count, limit - new_count, ttl, 1}
"""


def build_response(client_id, count, remaining, reset_in, allowed):
    if allowed:
        message = "Request allowed!"
    else:
        message = "Rate limit exceeded! Bro, take a break! 🤡"
    status = 200 if allowed else 429
    return JSONResponse(
        status_code=status,
        content={
            "message": message,
            "count": count,
            "remaining": remaining,
            "limit": LIMIT,
            "reset_in": reset_in,
            "client_id": client_id,
            "allowed": allowed,
        },
    )


@app.get("/")
def home():
    return {"message": "Rate Limiter Backend is Running!"}


@app.get("/api/check")
def check_rate_limit(client_id: str = "default-client"):
    if redis_client is None:
        return JSONResponse(
            status_code=503,
            content={
                "message": "Rate limiter unavailable: Redis connection failed.",
                "error": "redis_connection_failed",
            },
        )

    key = f"ratelimit:{client_id}"

    try:
        result = redis_client.eval(CHECK_SCRIPT, 1, key, LIMIT, WINDOW)
        count = int(result[0])
        remaining = int(result[1])
        reset_in = int(result[2])
        allowed = int(result[3]) == 1
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "message": f"Rate limiter error: {exc}",
                "error": "redis_error",
            },
        )

    return build_response(client_id, count, remaining, reset_in, allowed)
