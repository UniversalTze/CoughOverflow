from sqlalchemy import Column, Integer, String
from .database import Base

## DATABASE model
class Labs(Base):
    __tablename__ = 'labs'
    id = Column(String, primary_key=True)