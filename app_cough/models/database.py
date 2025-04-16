import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL = "postgresql://user:password@localhost/dbname" # for locally hosted db
# URL = "postgresql://user:password@database/dbname" # for cotainer db
# SQLALCHEMY_DATABASE_URI = "postgresql://cough_user:superSecretPassword.23@database:5432/cough"
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
if not SQLALCHEMY_DATABASE_URI:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set in environment...")

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Ensure schemas exist before creating tables
#with async_engine.connect() as conn:
#    conn.execute(text("CREATE SCHEMA IF NOT EXISTS schema_a")) #Change schema_a and b
#    conn.execute(text("CREATE SCHEMA IF NOT EXISTS schema_b"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

