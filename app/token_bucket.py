from __future__ import annotations

import pathlib
import time
from typing import Any  # added

from redis.asyncio import Redis

SCRIPT_SHA: str | None = None
SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "rate_limiter.lua"


def _load_script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


async def ensure_script(redis: Redis) -> str:
    global SCRIPT_SHA
    if SCRIPT_SHA is None:
        SCRIPT_SHA = await redis.script_load(_load_script_text())
    return SCRIPT_SHA


async def allow(
    redis: Redis,
    key: str,
    capacity: int,
    rate: float,
    requested: int = 1,
) -> tuple[bool, float, int]:
    """
    Returns (allowed, tokens_after, retry_after_seconds)

    retry_after_seconds:
      0   -> request allowed OR immediately retryable
      >0  -> seconds client should wait before retrying
      -1  -> request can never be satisfied (requested > capacity or rate == 0)
    """
    sha = await ensure_script(redis)
    now_ms = int(time.time() * 1000)
    # Lua returns: allowed(int), tokens_after(number), retry_after(int)
    res: list[Any] = await redis.evalsha(
        sha,
        1,
        key,
        capacity,
        rate,
        now_ms,
        requested,
    )
    allowed_int, tokens_after_raw, retry_after_val = res
    allowed_flag = bool(int(allowed_int))
    tokens_after = float(tokens_after_raw)
    return allowed_flag, tokens_after, int(retry_after_val)
