from sqlalchemy import Column, String, Boolean, DateTime
from .database import Base
from datetime import datetime, timezone
## DATABASE model

class Request(Base): 
    __tablename__ = 'requests'
    request_id = Column(String, primary_key=True)
    lab_id = Column(String, index=True, nullable=False)
    patient_id = Column(String, index=True, nullable=False)
    result = Column(String, default="pending", nullable=False)
    urgent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, 
                        default=datetime.now(timezone.utc))

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