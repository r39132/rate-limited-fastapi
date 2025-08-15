
from __future__ import annotations
import asyncio
from typing import Tuple
from redis.asyncio import Redis
from pathlib import Path

SCRIPT_SHA: str | None = None

def _load_script_text() -> str:
    lua_path = Path(__file__).resolve().parent.parent / "rate_limiter.lua"
    return lua_path.read_text(encoding="utf-8")

async def ensure_script(redis: Redis) -> str:
    global SCRIPT_SHA
    if SCRIPT_SHA is None:
        SCRIPT_SHA = await redis.script_load(_load_script_text())
    return SCRIPT_SHA

async def allow(redis: Redis, key: str, capacity: int, rate: float) -> Tuple[bool, float, int]:
    sha = await ensure_script(redis)
    # EVALSHA returns [allowed, tokens_after, retry_after_ms]
    allowed, tokens_after, retry_ms = await redis.evalsha(sha, 1, key, capacity, rate)
    return bool(allowed), float(tokens_after), int(retry_ms)
