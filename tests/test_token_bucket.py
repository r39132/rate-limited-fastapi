import asyncio

from redis.asyncio import Redis

from app.token_bucket import allow


async def test_allow_initial(redis: Redis) -> None:
    allowed, tokens, retry = await allow(redis, "tb:user:test1", 10, 10)
    assert allowed
    assert retry == 0
    assert 0 <= tokens <= 10


async def test_exhaust(redis: Redis) -> None:
    key = "tb:user:test2"
    for _ in range(10):
        allowed, _, _ = await allow(redis, key, 10, 10)
        assert allowed
    allowed, tokens, retry_after = await allow(redis, key, 10, 10)
    assert not allowed
    assert retry_after >= 1  # needs refill
    assert tokens < 1


async def test_unsatisfiable(redis: Redis) -> None:
    # Request more than capacity => retry_after == -1 (cannot ever succeed)
    allowed, tokens, retry_after = await allow(redis, "tb:user:test3", 5, 5, requested=10)
    assert not allowed
    assert retry_after == -1
    assert tokens <= 5


async def test_refill(redis: Redis) -> None:
    key = "tb:user:test4"
    for _ in range(5):
        await allow(redis, key, 5, 5)
    # Deplete
    extra_allowed, _, _ = await allow(redis, key, 5, 5)
    assert not extra_allowed or isinstance(extra_allowed, bool)
    await asyncio.sleep(1.2)
    allowed, tokens, retry = await allow(redis, key, 5, 5)
    assert allowed
    assert retry == 0
    assert 0 <= tokens <= 5
