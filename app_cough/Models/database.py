from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL = "postgresql://user:password@localhost/dbname" # for locally hosted db
# URL = "postgresql://user:password@database/dbname" # for cotainer db
SQLALCHEMY_DATABASE_URL = "postgresql://cough_user:superSecretPassword.23@database:5432/cough"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
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

