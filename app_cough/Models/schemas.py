from pydantic import BaseModel
from typing import List

#For response schemas
class Labs(BaseModel): 
    labs: List[str]