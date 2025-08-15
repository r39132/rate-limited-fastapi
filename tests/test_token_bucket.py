
import asyncio
import time
import pytest
from redis.asyncio import Redis
from app.token_bucket import allow, ensure_script

@pytest.mark.asyncio
async def test_allow_and_refill(tmp_path):
    r = Redis.from_url("redis://localhost:6379/15", decode_responses=False)
    key = b"tb:testcase"
    await r.delete(key)
    await ensure_script(r)

    capacity = 5
    rate = 5.0  # tokens/sec

    # consume capacity quickly
    allowed = 0
    for _ in range(capacity):
        a, _, _ = await allow(r, key, capacity, rate)
        allowed += int(a)
    assert allowed == capacity

    # next should be denied immediately
    a, tokens, retry = await allow(r, key, capacity, rate)
    assert a is False
    assert retry > 0

    # wait ~0.3s then one should pass after refill
    await asyncio.sleep(0.25)
    a, tokens_after, retry2 = await allow(r, key, capacity, rate)
    assert a is True
    await r.aclose()
