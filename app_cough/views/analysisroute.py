import multiprocessing.process
import base64, uuid, subprocess, tempfile, subprocess, multiprocessing, os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.params import Query, Body
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db
from typing import Union
from app_cough import utils
from app_cough.views import worker

MIN_KB = 4 * 1000
MAX_KB = 150 * 1000

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
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    if (body is None):
        error = utils.create_error(schemas.ErrorTypeEnum.no_image)
        return JSONResponse(status_code=400, 
                            content=error)
    given_body = [params for params in body] # check given body params are correct
    if not utils.validate_body(args=given_body, required=req_body):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)

    if patient_id is None:
        error = utils.create_error(schemas.ErrorTypeEnum.missing_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if (len(patient_id) != utils.LENGTH_PATIENT_ID):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (lab_id is None):
        error = utils.create_error(schemas.ErrorTypeEnum.missing_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if not utils.is_valid_lab_id(lab_id, db): 
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    
    image  = body["image"]
    try: 
        decoded_img = base64.b64decode(image, validate=True)
    except (base64.binascii.Error, ValueError):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_image_encryption)
        return JSONResponse(status_code=400, 
                            content=error)
    size_img = len(decoded_img)
    if (size_img < MIN_KB or size_img > MAX_KB):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_image_size)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if not decoded_img.startswith(b"\xFF\xD8") or not decoded_img.endswith(b"\xFF\xD9"):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_image_format)
        return JSONResponse(status_code=400, 
                            content=error)
    
    id_req = str(uuid.uuid4())
    request = dbmodels.Request(
        request_id=id_req,
        lab_id = lab_id,
        patient_id=patient_id,
        result=schemas.StatusEnum.PENDING.value,
        urgent=urgent
    )
    db.add(request)
    db.commit()
    message = schemas.AnalysisPost(
        id=request.request_id,
        created_at=request.created_at.isoformat(timespec='seconds') + 'Z',
        updated_at=request.created_at.isoformat(timespec='seconds') + 'Z',
        status=request.result
    )
    # get the nessary stuff from request before closing connection for fork()
    db.close()

    # create a temp directory to store these results. 
    tmp_dir = tempfile.gettempdir()
    input_path = f"{tmp_dir}/{id_req}.jpg"
    output = f"{tmp_dir}/{id_req}.txt"
    # write decoded image to .jpeg file
    with open(input_path, "wb") as f:
        f.write(decoded_img)

    # Need to fork a process
    process = multiprocessing.Process(target=worker.worker_image, args=(input_path, output, id_req, tmp_dir))
    process.start()
    return JSONResponse(status_code=201, content=message.dict())

@analysisrouter.get('/analysis', response_model= schemas.Analysis) 
def get_request(request_id: str = Query(...), db: Session = Depends(get_db), request: Request= None):
    query = {"request_id"}
    query_params = request.query_params 
    if not utils.validate_query(query_params, query):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
    result = crud.get_requests(db, request_id)
    if result is None:
        return JSONResponse(status_code=404, 
                                content= {
                                    "error": "request id not found",
                                    "detail": "request id does not correspond to any submitted analysis requests"
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
    
@analysisrouter.put('/analysis',response_model= Union[schemas.Analysis, schemas.AnalysisUpdateError, schemas.AnalysisPostError])
def update_request(request_id: str = Query(...), lab_id: str = Query(...), 
                   db: Session = Depends(get_db), request: Request= None): 
    query = {"request_id", "lab_id"}
    query_params = request.query_params 
    if not utils.validate_query(given=query_params, required=query):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if (lab_id is None or request_id is None):
        return JSONResponse(status_code=400, 
                            content={
                                "error": "request id or lab id not found in query params",
                                "detail": "request id or lab id not found. These are required parameters for this service"
                            })
    labs = crud.get_valid_labs(db) # list of all object items
    ids = set(lab.id for lab in labs)
    if (lab_id not in ids):
        error = schemas.AnalysisUpdateError(detail="Invalid lab identifier.")
        return JSONResponse(status_code=400, 
                            content=error.dict())
    req = crud.get_requests(db, request_id) # (in a tuple sql-alchemy) 0th index is id and other one is empty
    if req is None: 
        return JSONResponse(status_code=404, 
                                content= {
                                    "error": "request id not found",
                                    "detail": "request id not found in database"
                                })
    # there is a valid result id and lab is valid, need to update the row. 
    req = crud.update_requests(db, req, lab_id) # refresh in update_request function
    info = schemas.Analysis(request_id=req.request_id,
                lab_id=req.lab_id,
                patient_id=req.patient_id,
                result=req.result,
                urgent=req.urgent,
                created_at=req.created_at.isoformat(timespec='seconds') + 'Z',
                updated_at=req.updated_at.isoformat(timespec='seconds') + 'Z')
    return JSONResponse(status_code=200, content=info.dict())
