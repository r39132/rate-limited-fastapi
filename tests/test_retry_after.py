import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, settings


@pytest.mark.asyncio
async def test_retry_after_header_present() -> None:
    # Manually trigger FastAPI startup/shutdown (since we use deprecated on_event handlers)
    await app.router.startup()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Make capacity + 1 calls to ensure at least one 429
            last_resp = None
            for _ in range(settings.tb_capacity + 1):
                last_resp = await client.get("/items")
            assert last_resp is not None
            assert last_resp.status_code == 429
            # Header casing is preserved; FastAPI returns 'Retry-After'
            assert "Retry-After" in last_resp.headers
            assert int(last_resp.headers["Retry-After"]) >= 1
    finally:
        await app.router.shutdown()
