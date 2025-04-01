from enum import Enum
from pydantic import BaseModel
from typing import List
from datetime import datetime

#For response schemas

##### Status
class StatusEnum(Enum): 
    PENDING = "pending"
    COVID = "covid"
    H5N1 = "h5n1"
    HEALTHY = "healthy"
    FAILED = "failed"

##### Labs
class Labs(BaseModel): 
    labs: List[str]
    class Config:
        from_attributes = True  # This allows FastAPI to convert SQLAlchemy models to Pydantic models


##### Analysis
class Analysis(BaseModel): 
    request_id: str
    lab_id: str
    patient_id: str
    result: str
    urgent: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True  # This allows FastAPI to convert SQLAlchemy models to Pydantic models

class AnalysisPost(BaseModel): 
    id: str
    created_at: str
    updated_at: str
    status: str

    class Config:
        from_attributes = True  # This allows FastAPI to convert SQLAlchemy models to Pydantic models

###### Results
class ResultPatient(BaseModel): 
    results: List[Analysis]

###### Errors
class ErrorTypeEnum(Enum): 
    missing_patient_id = "Could not find patient ID"
    invalid_pateint_id =  "Incorrect format of patient ID"
    missing_lab_id = "Could not find Lab ID in DB"
    invalid_lab_id = "Invalid lab identifier"
    no_image = "Could not find Image"
    invalid_image = "Image needs to between this range(KB): 4  < img_size < 150"
    unknown_error = "Unknown error occured when processing request" 

class AnalysisPostError(BaseModel): 
    error: str   # Should be an enum from the list. 
    detail: str   # Additional info about the error. 

class AnalysisUpdateError(BaseModel): 
    detail: str