import base64, uuid
from datetime import datetime, timezone
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
        error = create_error(schemas.ErrorTypeEnum.missing_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (lab_id is None):
        error = create_error(schemas.ErrorTypeEnum.missing_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (body is None):
        error = create_error(schemas.ErrorTypeEnum.no_image)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (len(patient_id) != LENGTH_PATIENT_ID):
        error = create_error(schemas.ErrorTypeEnum.invalid_pateint_id)
        return JSONResponse(status_code=400, 
                            content=error)
    image  = body["image"]
    decoded_img = base64.b64decode(image)
    size_img = len(decoded_img)
    if (size_img < MIN_KB and size_img > MAX_KB):
        error = create_error(schemas.ErrorTypeEnum.invalid_image)
        return JSONResponse(status_code=400, 
                            content=error)
    
    labs = crud.get_valid_labs(db) # list of all object items
    ids = set(lab.id for lab in labs)
    if (lab_id not in ids): 
        error = create_error(schemas.ErrorTypeEnum.invalid_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace("+00:00", "Z")
    request = dbmodels.Request(
        request_id=str(uuid.uuid4()),
        lab_id = lab_id,
        patient_id=patient_id,
        result=schemas.StatusEnum.PENDING.value,
        urgent=urgent,

    )
    db.add(request)
    db.commit()
    message = schemas.AnalysisPost(
        id=request.request_id,
        created_at=request.created_at,
        updated_at=request.created_at,
        status=request.result
    )
    return JSONResponse(status_code=201, content=message.dict())
    #Post 201 into database now

def create_error(incorrect: schemas.ErrorTypeEnum): 
    invalid = schemas.AnalysisPostError(error=incorrect.name, detail=incorrect.value)
    return {"error": invalid.error,
            "detail": invalid.detail}
