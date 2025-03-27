from sqlalchemy import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# URL = "postgresql://user:password@localhost/dbname"
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://user:9F)6,A$E2egQ@database:5432/cough"

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine)
Base = declarative_base()

# Ensure schemas exist before creating tables
with async_engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS schema_a")) #Change schema_a and b
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS schema_b"))

def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        db.close()