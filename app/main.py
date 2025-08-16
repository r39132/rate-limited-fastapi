from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response
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
    latency_ms: float | None = None


rolling: list[Metrics] = []


def _client_id(req: Request) -> str:
    # Simple per-IP; adjust as needed
    return req.client.host if req.client else "unknown"


@app.on_event("startup")
async def startup() -> None:
    global redis
    redis = Redis.from_url(settings.redis_url, decode_responses=False)


@app.on_event("shutdown")
async def shutdown() -> None:
    global redis
    if redis is not None:
        await redis.close()
        redis = None


@app.middleware("http")
async def rate_limit_mw(
    request: Request,
    call_next: Callable[[Request], Awaitable[Any]],
) -> Response:
    if request.url.path == "/metrics":
        return await call_next(request)
    assert redis is not None
    cid = _client_id(request)
    key = f"{settings.bucket_prefix}{cid}"
    allowed_flag, tokens_after, retry_ms = await allow(
        redis, key, settings.tb_capacity, settings.tb_rate
    )
    headers: dict[str, str] = {
        "X-RateLimit-Capacity": str(settings.tb_capacity),
        "X-RateLimit-Rate": str(settings.tb_rate),
        "X-RateLimit-Remaining": f"{tokens_after:.2f}",
    }
    now_ts = time.time()
    if not allowed_flag:
        headers["Retry-After"] = f"{max(1, int((retry_ms + 999)//1000))}"
        rolling.append(Metrics(ts=now_ts, allowed=0, blocked=1, tokens=tokens_after))
        _prune_metrics(now_ts)
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429, headers=headers)

    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start) * 1000.0
    for k, v in headers.items():
        response.headers[k] = v
    rolling.append(
        Metrics(ts=now_ts, allowed=1, blocked=0, tokens=tokens_after, latency_ms=latency_ms)
    )
    _prune_metrics(now_ts)
    return response


@app.get("/items")
async def items() -> dict[str, Any]:
    return {"ok": True, "ts": time.time()}


@app.get("/metrics")
async def metrics() -> dict[str, Any]:
    return {
        "points": [m.model_dump() for m in rolling],
        "capacity": settings.tb_capacity,
        "rate": settings.tb_rate,
    }


def _prune_metrics(now_ts: float) -> None:
    cutoff = now_ts - settings.metrics_max_age_seconds
    while rolling and rolling[0].ts < cutoff:
        rolling.pop(0)
