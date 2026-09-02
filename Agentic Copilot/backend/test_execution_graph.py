import asyncio
from app.services.observability.graph_builder import build_execution_graph
from app.core.database import async_session_maker
from app.models.models import CustomerSession
from sqlalchemy import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(CustomerSession).order_by(CustomerSession.created_at.desc()).limit(1))
        session = res.scalar_one_or_none()
        if session:
            print("SESSION ID:", session.session_id)
            graph = await build_execution_graph(session.session_id, db)
            for node in graph["nodes"]:
                if node["id"] == "n_product_intelligence":
                    print("PI NODE STATUS:", node["status"])
                    print("PI NODE DETAILS:", node["details"])

if __name__ == "__main__":
    asyncio.run(main())
