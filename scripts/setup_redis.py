
#!/usr/bin/env python3
import asyncio
from redis.asyncio import Redis
from pathlib import Path

async def main():
    r = Redis.from_url("redis://localhost:6379/0", decode_responses=False)
    lua = (Path(__file__).resolve().parents[1] / "rate_limiter.lua").read_text(encoding="utf-8")
    sha = await r.script_load(lua)
    print("Loaded rate_limiter.lua SHA:", sha)
    await r.aclose()

if __name__ == "__main__":
    asyncio.run(main())
