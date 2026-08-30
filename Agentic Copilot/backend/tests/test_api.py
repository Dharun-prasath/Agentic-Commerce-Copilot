import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio

async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

async def test_dashboard_unauthorized():
    from app.core.config import settings
    original_key = settings.DASHBOARD_API_KEY
    settings.DASHBOARD_API_KEY = "test-key"
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
            response = await async_client.get("/api/v1/dashboard/stats")
            assert response.status_code == 401
            
            headers = {"X-API-Key": "wrong-key"}
            response = await async_client.get("/api/v1/dashboard/stats", headers=headers)
            assert response.status_code == 401
    finally:
        settings.DASHBOARD_API_KEY = original_key

async def test_telegram_webhook_invalid_format():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        # Telegram webhooks should return 200 even for unparseable data to avoid retry storms
        response = await async_client.post("/api/v1/integrations/telegram/webhook", json={})
        assert response.status_code == 200
