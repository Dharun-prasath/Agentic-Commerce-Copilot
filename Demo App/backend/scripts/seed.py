import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.models import (
    Base, Category, Brand, Series, ProductModel, Product, ProductImage, 
    ProductCompatibility, CompatibilityType
)
import uuid
import random

engine = create_async_engine(settings.async_database_url, echo=False)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

def get_image(name: str, brand: str = "", sku_variant: str = "", is_accessory: bool = False) -> str:
    n = name.lower()
    sku = sku_variant.lower()
    
    if is_accessory:
        if "mx master" in n: return "/images/products/logitech_mx_master_3s.png"
        if "magic mouse" in n: return "/images/products/apple_magic_mouse.png"
        if "mouse" in n: return "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&q=80"
        
        if "t7" in n: return "/images/products/samsung_t7_ssd.png"
        if "ssd" in n: return "https://images.unsplash.com/photo-1600861194942-f883de0dfe96?w=800&q=80"
        
        if "hdmi" in n: return "/images/products/usb_c_hdmi.png"
        if "satechi" in n: return "/images/products/satechi_adapter.png"
        if "dell" in n and "dock" in n: return "/images/products/dell_dock.png"
        if "thinkpad" in n and "dock" in n: return "/images/products/thinkpad_dock.png"
        
        if "keyboard" in n: return "https://images.unsplash.com/photo-1595225476474-87563907a212?w=800&q=80"
        if "monitor" in n or "display" in n: return "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&q=80"
        if "dock" in n or "adapter" in n or "hub" in n: return "https://images.unsplash.com/photo-1616423640778-28d1b53229bd?w=800&q=80"
        if "sleeve" in n or "bag" in n: return "https://images.unsplash.com/photo-1601666699310-096a750058e1?w=800&q=80"
        if "headset" in n or "headphones" in n: return "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=800&q=80"
        return "https://images.unsplash.com/photo-1531061994119-95240210f9e1?w=800&q=80" 
        
    if brand == "Apple": 
        if "black" in sku or "midnight" in sku:
            return "/images/products/macbook_space_black.png"
        return "/images/products/apple_macbook.png"
    if brand == "Dell": 
        return "/images/products/dell_xps.png"
    if brand == "HP":
        return "/images/products/hp_spectre.png"
    if brand == "Lenovo" and "thinkpad" in n:
        return "/images/products/thinkpad.png"
    if "rog" in n or "gaming" in n or "alienware" in n or "legion" in n or "predator" in n or "nitro" in n or brand in ["ASUS", "MSI"]:
        return "/images/products/gaming_laptop.png"
    
    return "/images/products/apple_macbook.png"

CATEGORIES = [
    {"name": "Laptops", "slug": "laptops", "icon": "", "description": "All laptops"},
    {"name": "Laptop Accessories", "slug": "laptop-accessories", "icon": "", "description": "Accessories"},
]

# Structure: Brand -> Series -> Model -> SKUs (Variants)
HIERARCHY = {
    "Apple": {
        "MacBook Air": {
            "MacBook Air 13\"": [
                "M5 / 16GB / 512GB / Sky Blue", "M5 / 16GB / 512GB / Silver", 
                "M5 / 16GB / 512GB / Starlight", "M5 / 16GB / 512GB / Midnight",
                "M5 / 24GB / 512GB / Sky Blue", "M5 / 24GB / 1TB / Silver",
                "M5 / 32GB / 1TB / Midnight", "M5 / 32GB / 2TB / Starlight"
            ],
            "MacBook Air 15\"": [
                "M5 / 16GB / 512GB / Sky Blue", "M5 / 16GB / 512GB / Silver",
                "M5 / 24GB / 1TB / Midnight", "M5 / 32GB / 1TB / Starlight",
                "M5 / 32GB / 2TB / Silver"
            ]
        },
        "MacBook Pro": {
            "MacBook Pro 14\"": [
                "M5 / 16GB / 512GB / Space Black", "M5 / 24GB / 1TB / Silver",
                "M5 Pro / 24GB / 1TB / Space Black", "M5 Pro / 48GB / 1TB / Silver",
                "M5 Max / 36GB / 1TB / Space Black", "M5 Max / 64GB / 2TB / Silver"
            ],
            "MacBook Pro 16\"": [
                "M5 Pro / 24GB / 1TB / Space Black", "M5 Pro / 48GB / 1TB / Silver",
                "M5 Max / 36GB / 1TB / Space Black", "M5 Max / 64GB / 2TB / Silver",
                "M5 Max / 128GB / 4TB / Space Black"
            ]
        }
    },
    "Dell": {
        "Inspiron": {
            "Inspiron 14": [
                "Core 5 / 8GB / 512GB / FHD / Platinum", "Core 5 / 16GB / 512GB / FHD / Platinum",
                "Core 7 / 16GB / 1TB / FHD+ / Silver", "Core Ultra 5 / 16GB / 512GB / FHD+ / Silver",
                "Ryzen 5 / 16GB / 512GB / FHD / Silver"
            ],
            "Inspiron 15": [
                "Core i3 / 8GB / 512GB", "Core i5 / 8GB / 512GB",
                "Core i5 / 16GB / 512GB", "Ryzen 5 / 16GB / 512GB"
            ],
            "Inspiron 16": [
                "Core 5 / 16GB / 512GB", "Core 7 / 16GB / 1TB",
                "Core Ultra 5 / 16GB / 512GB", "Core Ultra 7 / 32GB / 1TB"
            ]
        },
        "XPS": {
            "XPS 13": [
                "Core Ultra 5 / 16GB / 512GB", "Core Ultra 7 / 16GB / 1TB",
                "Core Ultra 7 / 32GB / 1TB", "Core Ultra 7 / 32GB / 2TB"
            ],
            "XPS 14": [
                "Core Ultra 7 / 16GB / 1TB", "Core Ultra 7 / 32GB / 1TB",
                "Core Ultra 7 / 64GB / 2TB", "Core Ultra 7 + RTX / 32GB / 1TB"
            ],
            "XPS 16": [
                "Core Ultra 7 / 16GB / 1TB", "Core Ultra 7 / 32GB / 1TB",
                "Core Ultra 9 / 64GB / 2TB", "Core Ultra 9 + RTX / 64GB / 4TB"
            ]
        },
        "Latitude": {
            "Latitude 7450": ["Core Ultra 5 / 16GB / 512GB", "Core Ultra 7 / 32GB / 1TB"]
        },
        "Alienware": {
            "Alienware m16": ["Core Ultra 7 / 16GB / 1TB / RTX 5060", "Core Ultra 9 / 32GB / 2TB / RTX 5080"]
        }
    },
    "HP": {
        "Spectre": {
            "Spectre x360 14": ["Core Ultra 7 / 16GB / 1TB"],
            "Spectre x360 16": ["Core Ultra 7 / 32GB / 1TB"]
        },
        "OMEN": {
            "OMEN 16": ["Core i7 / 16GB / 1TB / RTX 4060", "Core i9 / 32GB / 1TB / RTX 4070"]
        }
    },
    "Lenovo": {
        "ThinkPad": {
            "ThinkPad X1 Carbon": ["Core Ultra 5 / 16GB / 512GB", "Core Ultra 7 / 32GB / 1TB"],
            "ThinkPad T14": ["Core Ultra 5 / 16GB / 512GB", "Core Ultra 7 / 32GB / 1TB"]
        },
        "Legion": {
            "Legion Pro 7i": ["Core Ultra 7 / 32GB / 1TB / RTX 5070", "Core Ultra 9 / 32GB / 2TB / RTX 5080"]
        }
    },
    "ASUS": {
        "ROG": {
            "ROG Strix G16": ["Core i7 / 16GB / 1TB / RTX 4060", "Core i9 / 32GB / 1TB / RTX 4070"],
            "ROG Zephyrus G14": ["Ryzen 9 / 32GB / 1TB / RTX 5070", "Ryzen 9 / 32GB / 2TB / RTX 5080"]
        },
        "Zenbook": {
            "Zenbook 14": ["Core Ultra 5 / 16GB / 512GB", "Core Ultra 7 / 16GB / 1TB"]
        }
    },
    "Acer": {
        "Predator": {
            "Predator Helios 16": ["Core Ultra 9 / 32GB / 1TB / RTX 5070", "Core Ultra 9 / 64GB / 2TB / RTX 5080"]
        }
    },
    "MSI": {
        "Raider": {
            "Raider 16": ["Core Ultra 9 / 32GB / 1TB / RTX 5070", "Core Ultra 9 / 64GB / 2TB / RTX 5080"]
        }
    }
}

ACCESSORIES_RAW = [
    # UNIVERSAL
    ("Logitech MX Master 3S", "UNIVERSAL", "ALL"),
    ("Samsung T7 1TB SSD", "UNIVERSAL", "ALL"),
    ("USB-C to HDMI Adapter", "REQUIRED_ADAPTER", "ALL"),
    
    # APPLE
    ("Apple Magic Mouse", "RECOMMENDED", "Apple"),
    ("Satechi Type-C Multi-Port Adapter", "COMPATIBLE", "Apple"),
    
    # DELL
    ("Dell WD22TB4 Thunderbolt 4 Dock", "COMPATIBLE", "Dell"),
    
    # LENOVO
    ("ThinkPad Universal USB-C Dock", "COMPATIBLE", "Lenovo"),
    
    # ASUS
    ("ASUS ROG Gladius III Mouse", "RECOMMENDED", "ASUS"),
    
    # SIZE MATCH (we will map these to specific models)
    ("Tomtoc 13-inch Laptop Sleeve", "SIZE_MATCH", ["MacBook Air 13\"", "XPS 13"]),
    ("Tomtoc 15/16-inch Laptop Sleeve", "SIZE_MATCH", ["MacBook Air 15\"", "MacBook Pro 16\"", "Inspiron 15", "XPS 15", "XPS 16"]),
]

async def seed():
    print("Starting hierarchical seed operation...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession() as session:
        # Categories
        cat_laptops = Category(name="Laptops", slug="laptops")
        cat_acc = Category(name="Accessories", slug="accessories")
        session.add_all([cat_laptops, cat_acc])
        await session.commit()

        # Parse hierarchy
        sku_map = {}
        model_name_map = {}

        for b_name, series_dict in HIERARCHY.items():
            b = Brand(name=b_name)
            session.add(b)
            await session.commit()

            for s_name, model_dict in series_dict.items():
                s = Series(name=s_name, brand_id=b.id)
                session.add(s)
                await session.commit()

                for m_name, sku_list in model_dict.items():
                    m = ProductModel(
                        name=m_name, 
                        series_id=s.id, 
                        category_id=cat_laptops.id,
                        description=f"The powerful {m_name} from the {b_name} {s_name} series."
                    )
                    session.add(m)
                    await session.commit()
                    model_name_map[m_name] = m.id

                    for sku_variant in sku_list:
                        # Extract specs from variant string
                        parts = [p.strip() for p in sku_variant.split("/")]
                        specs = {
                            "brand": b_name,
                            "series": s_name,
                            "model": m_name,
                            "variant": {
                                "processor": parts[0] if len(parts) > 0 else "Unknown",
                                "memory": parts[1] if len(parts) > 1 else "Unknown",
                                "storage": parts[2] if len(parts) > 2 else "Unknown",
                                "extra": parts[3] if len(parts) > 3 else ""
                            }
                        }
                        
                        slug_str = f"{b_name}-{m_name}-{sku_variant}".replace(" ", "-").replace("/", "-").replace('"', '').lower()
                        
                        p = Product(
                            product_model_id=m.id,
                            name=f"{m_name} - {sku_variant}",
                            slug=slug_str,
                            brand=b_name,
                            category_id=cat_laptops.id,
                            price=150000.0, # Dummy price for now
                            original_price=170000.0,
                            description=f"{b_name} {m_name} configured with {sku_variant}.",
                            specifications=specs,
                            stock=100,
                            is_featured=random.random() < 0.3,
                            is_trending=random.random() < 0.2,
                            is_best_seller=random.random() < 0.2
                        )
                        session.add(p)
                        await session.commit()
                        
                        img = ProductImage(product_id=p.id, url=get_image(m_name, brand=b_name, sku_variant=sku_variant), is_primary=True, sort_order=0)
                        session.add(img)
                        await session.commit()
                        
                        sku_map[slug_str] = p
                        if "products" not in locals():
                            products_by_brand = {}
                        products_by_brand.setdefault(b_name, []).append(p)
                        products_by_model = locals().get("products_by_model", {})
                        products_by_model.setdefault(m_name, []).append(p)
                        locals()["products_by_model"] = products_by_model

        # Accessories
        for a_name, c_type, targets in ACCESSORIES_RAW:
            a_slug = a_name.replace(" ", "-").lower()
            a = Product(
                name=a_name,
                slug=a_slug,
                brand="Accessory Brand",
                category_id=cat_acc.id,
                price=5000.0,
                original_price=6000.0,
                description=f"{a_name} accessory.",
                stock=500,
                is_featured=random.random() < 0.4,
                is_trending=random.random() < 0.3,
                is_best_seller=random.random() < 0.5
            )
            session.add(a)
            await session.commit()

            img = ProductImage(product_id=a.id, url=get_image(a_name, is_accessory=True), is_primary=True, sort_order=0)
            session.add(img)
            await session.commit()

            c_enum = getattr(CompatibilityType, c_type)

            if targets == "ALL":
                for sku in sku_map.values():
                    session.add(ProductCompatibility(source_product_id=sku.id, target_product_id=a.id, compatibility_type=c_enum))
            elif isinstance(targets, str): # Brand match
                if targets in products_by_brand:
                    for sku in products_by_brand[targets]:
                        session.add(ProductCompatibility(source_product_id=sku.id, target_product_id=a.id, compatibility_type=c_enum))
            elif isinstance(targets, list): # Model match
                for t_model in targets:
                    if t_model in locals().get("products_by_model", {}):
                        for sku in locals()["products_by_model"][t_model]:
                            session.add(ProductCompatibility(source_product_id=sku.id, target_product_id=a.id, compatibility_type=c_enum))

        await session.commit()
        print("Seed complete! Normalized hierarchy applied.")

if __name__ == "__main__":
    asyncio.run(seed())
