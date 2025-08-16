import asyncio

from redis.asyncio import Redis

from app.token_bucket import allow


async def test_allow_initial(redis: Redis) -> None:
    allowed, tokens, _ = await allow(redis, "tb:user:test1", 10, 10)
    assert allowed
    assert 0 <= tokens <= 10


async def test_exhaust(redis: Redis) -> None:
    key = "tb:user:test2"
    for _ in range(10):
        allowed, _, _ = await allow(redis, key, 10, 10)
        assert allowed
    allowed, tokens, retry = await allow(redis, key, 10, 10)
    assert not allowed
    assert tokens < 1
    assert retry >= 0


async def test_refill(redis: Redis) -> None:
    key = "tb:user:test3"
    for _ in range(10):
        await allow(redis, key, 10, 5)
    await asyncio.sleep(1.2)
    allowed, tokens, _ = await allow(redis, key, 10, 5)
    assert allowed
    assert tokens <= 10
