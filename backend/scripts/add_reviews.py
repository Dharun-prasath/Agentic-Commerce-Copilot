import asyncio
import os
import sys
import random
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.models import Product, ProductReview
from sqlalchemy import select

REVIEWERS = [
    "Alex M.", "Sarah T.", "John D.", "Emily R.", "Michael B.",
    "Jessica L.", "David K.", "Amanda W.", "Chris P.", "Samantha H.",
    "Kevin G.", "Laura N.", "Ryan C.", "Melissa F.", "Daniel S."
]

TITLES_GOOD = [
    "Excellent product", "Highly recommended!", "Amazing performance",
    "Worth every penny", "Best laptop I've owned", "Incredible machine",
    "Flawless experience", "Fast and reliable", "Great value", "Perfect!"
]
BODIES_GOOD = [
    "I've been using this for a few weeks now and it's absolutely fantastic. It handles all my workloads without breaking a sweat.",
    "The build quality is premium and the performance is top-notch. Battery life is also very impressive.",
    "Exceeded my expectations. The screen is gorgeous and the keyboard is very comfortable.",
    "Super fast, quiet, and reliable. I use it daily for heavy tasks and it never slows down.",
    "A fantastic purchase. The delivery was quick and the product itself is exactly as described. Love it!"
]

TITLES_MID = [
    "Good but has flaws", "Decent laptop", "Meets expectations", "Solid machine", "Not bad"
]
BODIES_MID = [
    "Overall a good laptop, but the battery life could be a bit better. Still satisfied.",
    "Performance is great, but it gets a little warm under heavy load. Good for the price though.",
    "It does the job well. The screen is nice but the trackpad feels a bit cheap.",
    "A solid performer, but there are better options if you spend a little more. Still happy with it.",
    "Nice design and fast processor, but the webcam quality is lacking."
]

TITLES_BAD = [
    "Disappointing", "Not worth it", "Overpriced", "Has issues", "Regret buying"
]
BODIES_BAD = [
    "I had high hopes, but it freezes occasionally and the battery drains too fast.",
    "The build quality feels cheap for this price point. I wouldn't recommend it.",
    "Had some software issues out of the box. Customer support wasn't very helpful either.",
    "Gets way too hot when doing basic tasks. Very disappointing purchase.",
    "The screen has terrible backlight bleeding. Returning it."
]


async def add_random_reviews():
    async with AsyncSessionLocal() as db:
        # Delete existing reviews to start fresh
        await db.execute(select(ProductReview).with_only_columns(ProductReview.id)) # Just doing a quick way
        # Actually better to just delete all
        from sqlalchemy import delete
        await db.execute(delete(ProductReview))
        
        result = await db.execute(select(Product))
        products = result.scalars().all()
        
        total_reviews_added = 0

        for p in products:
            num_reviews = random.randint(5, 45)
            
            total_rating = 0
            reviews_for_p = []
            
            for _ in range(num_reviews):
                # Weighted random rating (more likely to be good)
                rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 30, 40], k=1)[0]
                total_rating += rating
                
                if rating >= 4:
                    title = random.choice(TITLES_GOOD)
                    body = random.choice(BODIES_GOOD)
                elif rating == 3:
                    title = random.choice(TITLES_MID)
                    body = random.choice(BODIES_MID)
                else:
                    title = random.choice(TITLES_BAD)
                    body = random.choice(BODIES_BAD)
                
                review = ProductReview(
                    id=str(uuid4()),
                    product_id=p.id,
                    reviewer_name=random.choice(REVIEWERS),
                    rating=rating,
                    title=title,
                    body=body,
                    is_verified_purchase=random.choice([True, True, True, False]), # 75% verified
                    helpful_count=random.randint(0, 15)
                )
                reviews_for_p.append(review)
                total_reviews_added += 1
            
            db.add_all(reviews_for_p)
            
            # Update product aggregates
            p.review_count = num_reviews
            p.rating = round(total_rating / num_reviews, 1)

        print(f"Committing {total_reviews_added} reviews...")
        await db.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(add_random_reviews())
