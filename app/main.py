from __future__ import annotations
import time
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis

from .config import settings
from .token_bucket import allow

app = FastAPI(title="Rate-limited FastAPI")

redis: Redis | None = None

class Metrics(BaseModel):
    ts: float
    allowed: int
    blocked: int
    tokens: float

# In-memory rolling metrics (for demo); also expose via /metrics
rolling: list[Metrics] = []

def _client_id(req: Request) -> str:
    # Simple: use client host; swap for API key/header in real use
    ip = req.client.host if req.client else "unknown"
    return ip

@app.on_event("startup")
async def startup() -> None:
    global redis
    redis = Redis.from_url(settings.redis_url, decode_responses=False)

@app.on_event("shutdown")
async def shutdown() -> None:
    if redis:
        await redis.aclose()

@app.middleware("http")
async def rate_limit_mw(request: Request, call_next):
    # Exclude dashboard metrics endpoint from rate limiting
    if request.url.path == "/metrics":
        return await call_next(request)
    assert redis is not None
    cid = _client_id(request)
    key = f"{settings.bucket_prefix}{cid}".encode()
    allowed_flag, tokens_after, retry_ms = await allow(redis, key, settings.tb_capacity, settings.tb_rate)

    headers: Dict[str, str] = {
        "X-RateLimit-Capacity": str(settings.tb_capacity),
        "X-RateLimit-Rate": str(settings.tb_rate),
        "X-RateLimit-Remaining": f"{tokens_after:.2f}",
    }
    if not allowed_flag:
        headers["Retry-After"] = f"{max(1, int((retry_ms+999)//1000))}"
        rolling.append(Metrics(ts=time.time(), allowed=0, blocked=1, tokens=tokens_after))
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429, headers=headers)

    response = await call_next(request)
    for k, v in headers.items():
        response.headers[k] = v
    rolling.append(Metrics(ts=time.time(), allowed=1, blocked=0, tokens=tokens_after))
    if len(rolling) > 1000:
        rolling.pop(0)
    return response

@app.get("/items")
async def items() -> dict[str, Any]:
    return {"ok": True, "ts": time.time()}

@app.get("/metrics")
async def metrics() -> dict[str, Any]:
    # Return last N points
    points = [m.dict() for m in rolling[-300:]]
    return {"points": points, "capacity": settings.tb_capacity, "rate": settings.tb_rate}
