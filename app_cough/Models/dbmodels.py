from sqlalchemy import Column, String, Boolean
from .database import Base
from datetime import datetime, timezone
## DATABASE model
class Labs(Base):
    __tablename__ = 'labs'
    id = Column(String, primary_key=True)

class Request(Base): 
    __tablename__ = 'requests'
    request_id = Column(String, primary_key=True)
    lab_id = Column(String, index=True, nullable=False)
    patient_id = Column(String, index=True, nullable=False)
    result = Column(String, default="pending", nullable=False)
    urgent = Column(Boolean, default=False, nullable=False)
    created_at = Column(String, nullable=False, default=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'))
    updated_at = Column(String, nullable=False, 
                        default=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'), 
                        onupdate=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'))

    def to_dict(self): 
        return { 
            "request_id": self.request_id,
            "lab_id": self.lab_id,
            "patient_id": self.patient_id,
            "result": self.result, 
            "urgent": self.urgent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }