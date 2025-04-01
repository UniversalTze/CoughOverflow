import base64, uuid
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.params import Query, Body
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db
from typing import Union
from app_cough import utils

LENGTH_PATIENT_ID = 11
MIN_KB = 4 * 1000
MAX_KB = 15 * 1000

analysisrouter = APIRouter()

@analysisrouter.post('/analysis', response_model= Union[schemas.AnalysisPost, schemas.AnalysisPostError])
def create_analysis(patient_id: str = Query(None, description="patient_id"), 
                    lab_id: str = Query(None, description="lab_id"), 
                    urgent: bool = Query(None, description="urgent"),
                    body: dict = Body(None), 
                    db: Session = Depends(get_db), 
                    request: Request= None): 
    query = {"patient_id", "lab_id", "urgent"}
    req_body = {"image"}
    query_params = request.query_params
    if not utils.validate_query(query_params, required=query):
        error = create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
    given_body = [params for params in body]
    if not utils.validate_body(args=given_body, required=req_body) or isinstance(body, list):
        error = create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)

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
    
    request = dbmodels.Request(
        request_id=str(uuid.uuid4()),
        lab_id = lab_id,
        patient_id=patient_id,
        result=schemas.StatusEnum.PENDING.value,
        urgent=urgent
    )
    db.add(request)
    db.commit()

    # @TODO need to fork a process here to exec Cough Overflow engine. (function in crud.py) 
    message = schemas.AnalysisPost(
        id=request.request_id,
        created_at=request.created_at.isoformat(timespec='seconds') + 'Z',
        updated_at=request.created_at.isoformat(timespec='seconds') + 'Z',
        status=request.result
    )
    return JSONResponse(status_code=201, content=message.dict())

@analysisrouter.get('/analysis', response_model= schemas.Analysis) 
def get_request(request_id: str = Query(...), db: Session = Depends(get_db), request: Request= None):
    query = {"request_id"}
    query_params = request.query_params 
    if not utils.validate_query(query_params, query):
        error = create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
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
            created_at=result.created_at.isoformat(timespec='seconds') + 'Z',
            updated_at=result.updated_at.isoformat(timespec='seconds') + 'Z',
        )
    return JSONResponse(status_code=200, 
                                content=info.dict())
    
@analysisrouter.put('/analysis') # response_model= Union[schemas.AnalysisPost, schemas.AnalysisUpdateError])
def update_request(request_id: str = Query(...), lab_id: str = Query(...), 
                   db: Session = Depends(get_db), request: Request= None): 
    query = {"patient_id", "lab_id"}
    query_params = request.query_params 
    if not utils.validate_query(given_params=query_params, required=query):
        error = create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
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
                created_at=result.created_at.isoformat(timespec='seconds') + 'Z',
                updated_at=result.updated_at.isoformat(timespec='seconds') + 'Z')
    return JSONResponse(status_code=200, content=info.dict())

def create_error(incorrect: schemas.ErrorTypeEnum): 
    invalid = schemas.AnalysisPostError(error=incorrect.name, detail=incorrect.value)
    return {"error": invalid.error,
            "detail": invalid.detail}
