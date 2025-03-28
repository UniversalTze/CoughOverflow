from sqlalchemy import Column, Integer, String
from .database import Base

## DATABASE model
class Labs(Base):
    __tablename__ = 'labs'
    id = Column(String, primary_key=True)

class Request(Base): 
    __tablename__ = 'request'
    patient_id = Column(String, primary_key=True)
    lab_id = Column(String, index=True)
    urgent = Column(bool)