import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# URL = "postgresql://user:password@localhost/dbname" # for locally hosted db
# URL = "postgresql://user:password@database/dbname" # for cotainer db
# SQLALCHEMY_DATABASE_URI = "postgresql://cough_user:superSecretPassword.23@database:5432/cough"
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
if not SQLALCHEMY_DATABASE_URI:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set in environment...")

engine = create_async_engine(SQLALCHEMY_DATABASE_URI, echo=True, pool_size=15, max_overflow=15)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

