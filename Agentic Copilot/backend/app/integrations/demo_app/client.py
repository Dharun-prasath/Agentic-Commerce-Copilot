import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DemoCommerceClient:
    """Client to interact with the existing Demo App REST API."""
    
    def __init__(self, base_url: str = settings.DEMO_APP_BASE_URL):
        self.base_url = base_url
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from Demo App: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise

    async def get_products(self, query_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("GET", "/products", params=query_params)
        
    async def get_product(self, slug: str) -> Dict[str, Any]:
        return await self._request("GET", f"/products/{slug}")

    async def search_products_autocomplete(self, query: str) -> Dict[str, Any]:
        return await self._request("GET", "/products/search/suggestions", params={"q": query})
        
    async def get_categories(self) -> List[Dict[str, Any]]:
        return await self._request("GET", "/products/categories")

    async def get_cart(self, session_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        headers = {"X-Session-Id": session_id}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return await self._request("GET", "/cart", headers=headers)

    async def add_to_cart(self, session_id: str, product_id: str, quantity: int, token: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        headers = {"X-Session-Id": session_id}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if user_id:
            headers["X-User-Id"] = user_id
        payload = {"product_id": product_id, "quantity": quantity}
        return await self._request("POST", "/cart/items", json=payload, headers=headers)
