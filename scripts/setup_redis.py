#!/usr/bin/env python3
import asyncio
from pathlib import Path

from redis.asyncio import Redis


async def main() -> None:
    r = Redis.from_url("redis://localhost:6379/0", decode_responses=False)
    lua = (Path(__file__).resolve().parents[1] / "rate_limiter.lua").read_text(encoding="utf-8")
    sha = await r.script_load(lua)
    print("Loaded rate_limiter.lua SHA:", sha)
    # redis.asyncio.Redis uses close(), not aclose(), in type stubs
    await r.close()


if __name__ == "__main__":
    asyncio.run(main())
