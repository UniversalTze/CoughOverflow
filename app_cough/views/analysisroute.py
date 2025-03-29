import base64
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.params import Query, Body
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db
from typing import Union


LENGTH_PATIENT_ID = 11
MIN_KB = 4 * 1024
MAX_KB = 15 * 1024

analysisrouter = APIRouter()

@analysisrouter.post('/analysis')  #response_model= schemas.AnalysisPostError) # Need create
def create_analysis(patient_id: str = Query(None, description="patient_id"), 
                    lab_id: str = Query(None, description="lab_id"), 
                    urgent: bool = Query(None, description="urgent"),
                    body: dict = Body(None), 
                    db: Session = Depends(get_db)):
    if patient_id is None:
        error = create_error(schemas.ErrorType.missing_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (lab_id is None):
        error = create_error(schemas.ErrorType.missing_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (body is None):
        error = create_error(schemas.ErrorType.no_image)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (len(patient_id) != LENGTH_PATIENT_ID):
        error = create_error(schemas.ErrorType.invalid_pateint_id)
        return JSONResponse(status_code=400, 
                            content=error)
    image  = body["image"]
    decoded_img = base64.b64decode(image)
    size_img = len(decoded_img)
    if (size_img < MIN_KB and size_img > MAX_KB):
        error = create_error(schemas.ErrorType.invalid_image)
        return JSONResponse(status_code=400, 
                            content=error)

    
    
    return 200

def create_error(incorrect: schemas.ErrorType): 
    invalid = schemas.AnalysisPostError(error=incorrect.name, detail=incorrect.value)
    return {"error": invalid.error,
            "detail": invalid.detail}
