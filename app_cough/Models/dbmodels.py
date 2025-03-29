from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

## DATABASE model
class Labs(Base):
    __tablename__ = 'labs'
    id = Column(String, primary_key=True)

class Request(Base): 
    __tablename__ = 'request'
    request_id = Column(String, primary_key=True)
    patient_id = Column(String, index=True)
    lab_id = Column(String, index=True)
    urgent = Column(Boolean, default=False)