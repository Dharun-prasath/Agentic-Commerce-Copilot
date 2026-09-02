import asyncio
from app.core.database import async_session_maker
from app.models.models import ConversationMessage, CustomerSession
from sqlalchemy import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(CustomerSession).order_by(CustomerSession.created_at.desc()).limit(1))
        session = res.scalar_one_or_none()
        if not session:
            return
            
        print(f"SESSION ID: {session.session_id}")
        
        # Get messages
        msg_res = await db.execute(
            select(ConversationMessage).where(ConversationMessage.conversation.has(session_id=session.session_id)).order_by(ConversationMessage.created_at)
        )
        msgs = msg_res.scalars().all()
        for m in msgs:
            print(f"{m.sender_type}: {m.content}")

if __name__ == "__main__":
    asyncio.run(main())
