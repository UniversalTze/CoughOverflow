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

class ResultSummary(BaseModel): 
    lab_id: str
    pending: int
    covid: int
    h5n1: int
    healthy: int
    failed: int
    urgent: int
    generated_at: str

###### Errors
class ErrorTypeEnum(Enum): 
    missing_patient_id = "Could not find patient ID in query. This needs to be provided to use this service"
    invalid_patient_id =  "Incorrect format or length of patient ID"
    missing_lab_id = "Could not find Lab ID in DB in query. This needs to be provided to use this service"
    invalid_lab_id = "Invalid lab identifier. Not apart of the available labs to use this service"
    no_image = "Could not find Image"
    invalid_image_size = "Image needs to between this range(KB): 4  < img_size < 150"
    invalid_image_encryption = "Invalid Base64 or corrupt image"
    invalid_image_format = "Image is not in Jpeg format"
    unknown_error = "Unknown error occured when processing request" 
    invalid_query = "Query parameters are malformed. Please check!"
    invalid_body = "Body arguments are malformed. Please check!"
    missing_request_id = "Request id is missing from query. Needs to be provided to use this service"

class AnalysisPostError(BaseModel): 
    error: str   # Should be an enum from the list. 
    detail: str   # Additional info about the error. 

class AnalysisUpdateError(BaseModel): 
    detail: str