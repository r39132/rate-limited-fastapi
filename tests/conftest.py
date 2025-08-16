from __future__ import annotations

import os
import warnings
from collections.abc import AsyncIterator

import pytest
from redis.asyncio import Redis

TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")

# Suppress deprecation warning if runtime prefers aclose()
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="Call to deprecated close",
)


@pytest.fixture
async def redis() -> AsyncIterator[Redis]:
    client = Redis.from_url(TEST_REDIS_URL, decode_responses=False)
    try:
        await client.ping()
    except Exception:
        pytest.skip("Redis server not available for tests")
    await client.flushdb()
    try:
        yield client
    finally:
        await client.close()
