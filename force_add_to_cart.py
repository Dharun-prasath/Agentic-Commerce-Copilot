import asyncio
import sys
import uuid
import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/agentic_commerce"

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 force_add_to_cart.py <product_id> [user_email]")
        print("Example: python3 force_add_to_cart.py bb362054-bbb4-4381-b483-4fbc9603e801")
        sys.exit(1)

    product_id = sys.argv[1]
    user_email = sys.argv[2] if len(sys.argv) > 2 else None

    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # 1. Verify the product exists
        res = await conn.execute(text("SELECT id, name FROM products WHERE id = :pid"), {"pid": product_id})
        product = res.fetchone()
        if not product:
            print(f"❌ Error: Product with ID {product_id} not found in the database.")
            return
        
        print(f"✅ Found product: {product.name} (ID: {product.id})")

        cart_id = None

        if user_email:
            # Add to specific user's cart
            res = await conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_email})
            user = res.fetchone()
            if not user:
                print(f"❌ Error: User with email {user_email} not found.")
                return
            
            user_id = user.id
            res = await conn.execute(text("SELECT id FROM carts WHERE user_id = :uid LIMIT 1"), {"uid": user_id})
            cart = res.fetchone()
            if cart:
                cart_id = cart.id
                print(f"✅ Found existing cart for {user_email}.")
            else:
                cart_id = str(uuid.uuid4())
                await conn.execute(
                    text("INSERT INTO carts (id, user_id, session_id, created_at, updated_at) VALUES (:cid, :uid, :sid, :now, :now)"),
                    {"cid": cart_id, "uid": user_id, "sid": str(uuid.uuid4()), "now": datetime.datetime.utcnow()}
                )
                print(f"✅ Created new cart for {user_email}.")
        else:
            # Find the most recently accessed/created cart in the system
            res = await conn.execute(text("SELECT id, user_id, session_id FROM carts ORDER BY created_at DESC LIMIT 1"))
            cart = res.fetchone()
            if cart:
                cart_id = cart.id
                print(f"✅ Found most recent cart (ID: {cart_id}, User: {cart.user_id}, Session: {cart.session_id}).")
            else:
                # Create a generic anonymous cart
                cart_id = str(uuid.uuid4())
                await conn.execute(
                    text("INSERT INTO carts (id, session_id, created_at, updated_at) VALUES (:cid, :sid, :now, :now)"),
                    {"cid": cart_id, "sid": "manual-script-session", "now": datetime.datetime.utcnow()}
                )
                print(f"✅ Created a new anonymous cart.")

        # 2. Add item to cart_items
        # Check if item already in cart
        res = await conn.execute(
            text("SELECT id, quantity FROM cart_items WHERE cart_id = :cid AND product_id = :pid"),
            {"cid": cart_id, "pid": product_id}
        )
        cart_item = res.fetchone()

        if cart_item:
            new_quantity = cart_item.quantity + 1
            await conn.execute(
                text("UPDATE cart_items SET quantity = :qty WHERE id = :item_id"),
                {"qty": new_quantity, "item_id": cart_item.id}
            )
            print(f"✅ Incremented quantity to {new_quantity} for {product.name} in cart {cart_id}.")
        else:
            item_id = str(uuid.uuid4())
            await conn.execute(
                text("INSERT INTO cart_items (id, cart_id, product_id, quantity) VALUES (:iid, :cid, :pid, 1)"),
                {"iid": item_id, "cid": cart_id, "pid": product_id}
            )
            print(f"✅ Added {product.name} to cart {cart_id}.")
            
    print("🎉 Success! The cart has been updated.")

if __name__ == "__main__":
    asyncio.run(main())
