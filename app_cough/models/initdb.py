from .database import engine
from app_cough.models import dbmodels
import asyncio
import asyncpg
import logging
import os

async def init_db():
    await wait_for_db(max_retries=10, delay=5)
    async with engine.begin() as conn:
        await conn.run_sync(dbmodels.Base.metadata.create_all)

async def wait_for_db(max_retries: int, delay:int):
    con_logger = logging.getLogger("DB Connection starup")
    con_logger.setLevel(level=logging.INFO)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set in environment...")
    DB_URI = SQLALCHEMY_DATABASE_URI.replace('postgresql+asyncpg', 'postgresql')
    for attempt in range(max_retries):
        con_logger.info("Attempting to connect to Postgress")
        try:
            conn = await asyncpg.connect(DB_URI)
            await conn.close()
            con_logger.info("Database is ready after successful connection")
            return
        except Exception as e:
            con_logger.info(f"Connection attempt {attempt+1} failed: {str(e)}")
            await asyncio.sleep(delay)
    raise RuntimeError("Database connection failed after retries.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())