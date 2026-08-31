import httpx
import logging
import json
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramProvider(ABC):
    @abstractmethod
    async def send_text(self, chat_id: str, text: str) -> bool:
        pass

    @abstractmethod
    async def send_product_card(self, chat_id: str, product: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def send_recommendation_summary(self, chat_id: str, summary: str, products: List[Dict[str, Any]]) -> bool:
        pass


class RealTelegramProvider(TelegramProvider):
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN is not configured!")
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    async def _post(self, endpoint: str, payload: Dict[str, Any]) -> bool:
        url = f"{self.api_url}/{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Telegram API error [{endpoint}]: {e}")
            return False

    async def send_text(self, chat_id: str, text: str) -> bool:
        if not self.token:
            return False
        return await self._post("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        })

    async def send_product_card(self, chat_id: str, product: Dict[str, Any]) -> bool:
        """Send a single beautifully formatted product card with inline button."""
        if not self.token:
            return False

        name = product.get("product_name", "Product")
        brand = product.get("brand", "")
        category = product.get("category", "")
        price = product.get("price", 0)
        original_price = product.get("original_price", 0)
        rating = product.get("rating", 0)
        review_count = product.get("review_count", 0)
        match_score = product.get("match_score", 0)
        match_reason = product.get("match_reason", "")
        key_features = product.get("key_features", [])
        product_url = product.get("product_url", "")

        image_url = product.get("image_url", "")

        # Build score indicator
        score_pct = int(match_score * 100)
        if score_pct >= 85:
            score_emoji = "🟢"
        elif score_pct >= 65:
            score_emoji = "🟡"
        else:
            score_emoji = "🔴"

        # Format price and discount
        price_formatted = f"₹{price:,.0f}" if price else "Price on request"
        discount_text = ""
        if original_price and original_price > price:
            discount_pct = int(((original_price - price) / original_price) * 100)
            discount_text = f" <s>₹{original_price:,.0f}</s> <b>({discount_pct}% OFF)</b>"

        # Format rating stars
        rating_stars = ""
        if rating:
            full_stars = int(rating)
            rating_stars = "⭐" * full_stars
            if rating - full_stars >= 0.5:
                rating_stars += "½"
            if review_count:
                rating_stars += f" {rating}/5 ({review_count} reviews)"
            else:
                rating_stars += f" {rating}/5"

        # Build features list
        features_text = ""
        if key_features:
            features_text = "\n".join([f"  • {f}" for f in key_features])

        # Build the HTML message card
        card_parts = [f"🛍️ <b>{name}</b>"]
        if brand:
            card_parts.append(f"🏷️ <b>Brand:</b> {brand}")
        if category:
            card_parts.append(f"📁 <b>Category:</b> {category}")
        card_parts.append("")
        card_parts.append(f"💰 <b>Price:</b> {price_formatted}{discount_text}")
        if rating_stars:
            card_parts.append(f"⭐ <b>Rating:</b> {rating_stars}")
        card_parts.append(f"{score_emoji} <b>AI Match Score:</b> {score_pct}%")
        card_parts.append("")
        card_parts.append(f"📋 <b>Why this product?</b>\n{match_reason}")

        if features_text:
            card_parts.append(f"\n✨ <b>Key Specs:</b>\n{features_text}")

        card_text = "\n".join(card_parts)

        # Build inline keyboard with product link button
        inline_keyboard = []
        if product_url:
            inline_keyboard.append([
                {"text": "🛒 View Product", "url": product_url}
            ])
            
        reply_markup = {"inline_keyboard": inline_keyboard} if inline_keyboard else None

        # If we have an image URL, try to download and send as a photo
        if image_url:
            try:
                base_url = settings.DEMO_APP_BASE_URL.replace("/api/v1", "")
                if image_url.startswith("/"):
                    full_image_url = f"{base_url}{image_url}"
                else:
                    full_image_url = f"{base_url}/{image_url}"
                
                async with httpx.AsyncClient(timeout=15) as client:
                    img_response = await client.get(full_image_url)
                    img_response.raise_for_status()
                    
                    # Send photo
                    url = f"{self.api_url}/sendPhoto"
                    data = {
                        "chat_id": chat_id,
                        "caption": card_text,
                        "parse_mode": "HTML"
                    }
                    if reply_markup:
                        data["reply_markup"] = json.dumps(reply_markup)
                        
                    files = {"photo": ("product.jpg", img_response.content, "image/jpeg")}
                    
                    post_resp = await client.post(url, data=data, files=files)
                    post_resp.raise_for_status()
                    logger.info(f"Telegram product card (with image) sent for '{name}' to {chat_id}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to send product card with image for '{name}', falling back to text: {e}")

        # Fallback to text message if no image or image failed
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": card_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        success = await self._post("sendMessage", payload)
        if success:
            logger.info(f"Telegram product card (text only) sent for '{name}' to {chat_id}")
        return success

    async def send_recommendation_summary(self, chat_id: str, summary: str, products: List[Dict[str, Any]]) -> bool:
        """Send a header summary followed by individual product cards."""
        if not self.token:
            return False

        count = len(products)
        header = (
            f"🤖 <b>AI Product Recommendations</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Found <b>{count} product{'s' if count != 1 else ''}</b> matching your requirements:\n\n"
            f"<i>{summary}</i>"
        )
        await self._post("sendMessage", {
            "chat_id": chat_id,
            "text": header,
            "parse_mode": "HTML"
        })

        # Send each product card
        for i, product in enumerate(products, 1):
            await self.send_product_card(chat_id, product)

        # Send footer
        await self._post("sendMessage", {
            "chat_id": chat_id,
            "text": f"📊 Showing {count} top recommendation{'s' if count != 1 else ''} based on your browsing behavior.",
            "parse_mode": "HTML"
        })
        return True

    # Backward compat shim
    async def send_product(self, chat_id: str, text: str, product_name: str, product_url: str, image_url: Optional[str] = None) -> bool:
        return await self.send_product_card(chat_id, {
            "product_name": product_name,
            "product_url": product_url,
            "match_reason": text,
            "price": 0,
            "match_score": 0,
            "key_features": []
        })


class DemoTelegramProvider(TelegramProvider):
    def __init__(self):
        logger.info("Initializing Demo Telegram Provider")

    async def send_text(self, chat_id: str, text: str) -> bool:
        logger.info(f"[DEMO TELEGRAM] To: {chat_id} | Message: {text}")
        return True

    async def send_product_card(self, chat_id: str, product: Dict[str, Any]) -> bool:
        logger.info(f"[DEMO TELEGRAM] To: {chat_id} | Product Card: {product.get('product_name')} | Price: {product.get('price')}")
        return True

    async def send_recommendation_summary(self, chat_id: str, summary: str, products: List[Dict[str, Any]]) -> bool:
        logger.info(f"[DEMO TELEGRAM] To: {chat_id} | Summary + {len(products)} product cards")
        return True

    async def send_product(self, chat_id: str, text: str, product_name: str, product_url: str, image_url: Optional[str] = None) -> bool:
        logger.info(f"[DEMO TELEGRAM] To: {chat_id} | Product: {product_name} | URL: {product_url}")
        return True


def get_telegram_provider() -> TelegramProvider:
    if settings.TELEGRAM_BOT_TOKEN:
        return RealTelegramProvider()
    return DemoTelegramProvider()
