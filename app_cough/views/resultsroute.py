from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.params import Query
from sqlalchemy.orm import Session
from app_cough.models import schemas, crud, dbmodels, database, get_db
from datetime import datetime
from app_cough import utils

resultRouter = APIRouter()
LOWEST_LIMIT = 0
DEFAULT_LIMIT = 100
HIGHEST_LIMIT = 1000
DEFAULT_OFFSET = 0
@resultRouter.get('/patients/results') #response_model = schemas.ResultPatient)
def get_patient_results(patient_id: str = Query(None, description="patient_id"),
                        start: str = Query(None, description="start"),
                        end: str = Query(None, description="end"),
                        status: str = Query(None, description="status"),
                        urgent: bool = Query(None, description="urgent"),
                        db:Session = Depends(get_db), 
                        request: Request= None):
    # filters are additive, if none, they should not be applied.
    query = {"patient_id", "start", "end", "status", "urgent"}
    params = request.query_params
    if not utils.validate_query(params, query):
        error = {"error": "Invalid query parameters",
                "detail": "Check to see if parameters were submitted correctly with same format, no duplicates and no extra params"}
        return JSONResponse(status_code=400, 
                            content=error)
    
    if patient_id is None or len(patient_id) != 11:
        error = {"error": "Invalid query parameters",
                "detail": "patient id must be supplied correctly when using this method"}
        return JSONResponse(status_code=400, 
                            content=error)
    # check valid status 
    if status is not None and not utils.is_valid_status(status):
        error = {"error": "Invalid query parameters",
                "detail": "status must be one of 'pending', 'covid', 'h5n1, 'healthy', 'failed'"}
        return JSONResponse(status_code=400, 
                            content=error)
    # check dates
    if start is not None:
        if not utils.is_valid_date(start):
            error = {"error": "Invalid query parameters", 
                     "detail": "start date must be of rfc3339 format "}
            return JSONResponse(status_code=400, 
                            content=error)
        else:
            start = datetime.fromisoformat(start)
    
    if end is not None:
        if not utils.is_valid_date(end):
            error = {"error": "Invalid query parameters", 
                     "detail": "end date must be of rfc3339 format "}
            return JSONResponse(status_code=400, 
                            content=error)
        else:
            end = datetime.fromisoformat(end)

    # if patient id not in database or no results assocaited with patient with parameters return 404 error. 
    patient = crud.get_patient_id(db, patient_id)
    optional = {
        "start_date": start,
        "end_date": end,
        "status": status,
        "urgent": urgent
    }

    res = crud.get_patient_results(db, patient_id, optional_params=optional)
    if patient is None or not res:
        error = {"error": "patient id does not correspond to a known patient",
                "detail": "No associated records with this patient id with given search parameters."}
        return JSONResponse(status_code=404, 
                            content=error)
    
    # Now need to make it returnable
    result = []
    for obj in res: 
        analysis = schemas.Analysis(
            request_id=obj.request_id,
            lab_id=obj.lab_id,
            patient_id=obj.patient_id,
            result=obj.result,
            urgent=obj.urgent,
            created_at=obj.created_at.isoformat(timespec='seconds') + 'Z',
            updated_at=obj.updated_at.isoformat(timespec='seconds') + 'Z'
        )
        result.append(analysis.dict())
    return JSONResponse(status_code=200, 
                            content = { 
                                "result": result
                            })

@resultRouter.get('/labs/results/{lab_id}')
def get_lab_results(lab_id: str,
                    limit: int = Query(None, description="limit"),
                    offset: int = Query(None, description="offset"),
                    start: str = Query(None, description="start"),
                    end: str = Query(None, description="end"),
                    patient_id: str = Query(None, description="patient_id"),
                    status: str = Query(None, description="status"),
                    urgent: bool = Query(None, description="urgent"),
                    db:Session = Depends(get_db),
                    request: Request = None):
    query = {"limit","offset",  "start", "end", "patient_id", "status", "urgent"}
    params = request.query_params
    if not utils.validate_query(params, query):
        error = {"error": "Invalid query parameters",
                "detail": "Check to see if parameters were submitted correctly with same format, no duplicates and no extra params"}
        return JSONResponse(status_code=400, 
                            content=error)
    #check lab id (required)
    if lab_id is None or not utils.is_valid_lab_id(lab_id, db):
        error = {"error": "Invalid query parameters",
                "detail": "lab_id has not been provided or is not apart of the valid list"}
        return JSONResponse(status_code=400, 
                            content=error)
    if limit is None: 
        limit = DEFAULT_LIMIT
    else:
        limit = determine_limit(limit)
    if offset is None:   # important if offset > limit return empty array
        offset = DEFAULT_OFFSET
    # Checking dates
    if start is not None:
        if not utils.is_valid_date(start):
            error = {"error": "Invalid query parameters", 
                     "detail": "start date must be of rfc3339 format"}
            return JSONResponse(status_code=400, 
                            content=error)
        else:
            start = datetime.fromisoformat(start)
    
    if end is not None:
        if not utils.is_valid_date(end):
            error = {"error": "Invalid query parameters", 
                     "detail": "end date must be of rfc3339 format"}
            return JSONResponse(status_code=400, 
                            content=error)
        else:
            end = datetime.fromisoformat(end)
    # Check Patient ID. 
    if (patient_id is not None and len(patient_id) != 11):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_pateint_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if (status is not None and not utils.is_valid_status(status)): 
        error = {"error": "Invalid query parameters",
                "detail": "status must be one of 'pending', 'covid', 'h5n1, 'healthy', 'failed'"}
        return JSONResponse(status_code=400, 
                            content=error)
    # add to a data dictionary:
    data = { 
        "limit": limit,
        "offset": offset,
        "start_date": start,
        "end_date": end,
        "patient_id": patient_id,
        "status": status,
        "urgent": urgent
    }
    lab_results = crud.get_lab_results(db, data, lab_id)
    result = []
    for obj in lab_results: 
        analysis = schemas.Analysis(
            request_id=obj.request_id,
            lab_id=obj.lab_id,
            patient_id=obj.patient_id,
            result=obj.result,
            urgent=obj.urgent,
            created_at=obj.created_at.isoformat(timespec='seconds') + 'Z',
            updated_at=obj.updated_at.isoformat(timespec='seconds') + 'Z'
        )
        result.append(analysis.dict())
    return JSONResponse(status_code=200, 
                        content = { 
                            "result": result
                            }) 
    
def determine_status(status: str):
    for enums in schemas.StatusEnum:
        if enums.value == status: 
            return enums

def determine_limit(lim: int):
    if (lim < 0):
        return 0
    if (lim > 1000): 
        return 1000