from .database import engine
from app_cough.models import dbmodels
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(dbmodels.Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())