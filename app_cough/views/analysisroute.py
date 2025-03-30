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
MIN_KB = 4 * 1000
MAX_KB = 15 * 1000

analysisrouter = APIRouter()

@analysisrouter.post('/analysis', response_model= Union[schemas.AnalysisPost, schemas.AnalysisPostError]) # Need create
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
        img_data=image
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

# "0d8b018f-5113-431d-a96e-1f6320a258e3" -> QML 
# "bf090fef-e195-4cb0-ae1b-be73c7d02616" -> ACL4013 (been updated twice so different time stamp)

@analysisrouter.get('/analysis', response_model= schemas.Analysis) 
def get_request(request_id: str = Query(...), db: Session = Depends(get_db)):
    result = crud.get_requests(db, request_id)
    if result is None:
        return JSONResponse(status_code=404, 
                                content= {
                                    "error": "request id not found",
                                    "detail": "request id not found in database"
                                })
    info = schemas.Analysis(
            request_id=result.request_id,
            lab_id=result.lab_id,
            patient_id=result.patient_id,
            result=result.result,
            urgent=result.urgent,
            created_at=result.created_at,
            updated_at=result.updated_at
        )
    return JSONResponse(status_code=200, 
                                content=info.dict())
    
@analysisrouter.put('/analysis') # response_model= Union[schemas.AnalysisPost, schemas.AnalysisUpdateError])
def update_request(request_id: str = Query(...), lab_id: str = Query(...), db: Session = Depends(get_db)):
    labs = crud.get_valid_labs(db) # list of all object items
    ids = set(lab.id for lab in labs)
    if (lab_id not in ids):
        error = schemas.AnalysisUpdateError(detail="Invalid lab identifier.")
        return JSONResponse(status_code=400, 
                            content=error.dict())
    req = crud.get_requests(db, request_id) # For request id
    if req is None: 
        return JSONResponse(status_code=404, 
                                content= {
                                    "error": "request id not found",
                                    "detail": "request id not found in database"
                                })
    # there is a result id and lab is valid, need to update the row. 
    data = {
        "request_id": request_id,
        "lab_id": lab_id
    }
    result = crud.update_requests(db, req, data)
    info = schemas.Analysis(request_id=result.request_id,
                lab_id=result.lab_id,
                patient_id=result.patient_id,
                result=result.result,
                urgent=result.urgent,
                created_at=result.created_at,
                updated_at=result.updated_at)
    return JSONResponse(status_code=200, content=info.dict())

def create_error(incorrect: schemas.ErrorTypeEnum): 
    invalid = schemas.AnalysisPostError(error=incorrect.name, detail=incorrect.value)
    return {"error": invalid.error,
            "detail": invalid.detail}
