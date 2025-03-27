from pydantic import BaseModel
from typing import List

#For response schemas
class Labs(BaseModel): 
    labs: List[str]
    class Config:
        orm_mode = True  # This allows FastAPI to convert SQLAlchemy models to Pydantic models
