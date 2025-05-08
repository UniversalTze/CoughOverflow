import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from app_cough.models import schemas, crud, dbmodels, database, get_db
from datetime import datetime
from app_cough import utils

import asyncio # @TODO delete this

LOWEST_LIMIT = 0
DEFAULT_LIMIT = 100
HIGHEST_LIMIT = 1000
DEFAULT_OFFSET = 0

resultRouter = APIRouter()
request_logs = logging.getLogger("app.requests")

@resultRouter.get('/patients/results') #response_model = schemas.ResultPatient)
async def get_patient_results(patient_id: str = Query(None, description="patient_id"),
                        start: str = Query(None, description="start"),
                        end: str = Query(None, description="end"),
                        status: str = Query(None, description="status"),
                        urgent: bool = Query(None, description="urgent"),
                        db:AsyncSession = Depends(get_db), 
                        request: Request= None):
    # check params given to ensure no duplicates and additional params provided
    request_logs.info(f"Begin get request for patient results at {utils.get_time()}")
    query = {"patient_id", "start", "end", "status", "urgent"}
    params = request.query_params
    if (params and not utils.validate_query(params, query)):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    if patient_id is None:
        error = utils.create_error(schemas.ErrorTypeEnum.missing_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if len(patient_id) != utils.LENGTH_PATIENT_ID:
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)

    # check valid status 
    if status is not None and not utils.is_valid_status(status):
        error = {"error": "Invalid query parameters for status",
                "detail": "status must be one of 'pending', 'covid', 'h5n1, 'healthy', 'failed'"}
        return JSONResponse(status_code=400, 
                            content=error)
    # check dates
    if start is not None:
        if not utils.is_valid_date(start):
            error = {"error": "Invalid query parameters for start date", 
                     "detail": "start date must be of rfc3339 format "}
            return JSONResponse(status_code=400, 
                            content=error)
        else:
            start = datetime.fromisoformat(start)
    
    if end is not None:
        if not utils.is_valid_date(end):
            error = {"error": "Invalid query parameters for end date", 
                     "detail": "end date must be of rfc3339 format "}
            return JSONResponse(status_code=400, 
                            content=error)
        else:
            end = datetime.fromisoformat(end)

    # if patient id not in database or no results assocaited with patient with parameters return 404 error. 
    patient = await crud.get_patient_id(db, patient_id)
    optional = {
        "start_date": start,
        "end_date": end,
        "status": status,
        "urgent": urgent
    }

    res = await crud.get_patient_results(db, patient_id, optional_params=optional)
    if patient is None or not res: # results is empty
        error = {"error": "patient id does not correspond to a known patient",
                "detail": "No associated records with this patient id with the given lookup parameters."}
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
            created_at=obj.created_at.isoformat(timespec='seconds').replace('+00:00','Z'),
            updated_at=obj.updated_at.isoformat(timespec='seconds').replace('+00:00','Z')
        )
        result.append(analysis.dict())
    
    request_logs.info(f"End of get request for patient results at {utils.get_time()}")
    return JSONResponse(status_code=200, 
                            content=result)

@resultRouter.get('/labs/results/{lab_id}')
async def get_lab_results(lab_id: str,
                    limit: int = Query(None, description="limit"),
                    offset: int = Query(None, description="offset"),
                    start: str = Query(None, description="start"),
                    end: str = Query(None, description="end"),
                    patient_id: str = Query(None, description="patient_id"),
                    status: str = Query(None, description="status"),
                    urgent: bool = Query(None, description="urgent"),
                    db:AsyncSession = Depends(get_db),
                    request: Request = None):
    #check lab id (required) found in path
    request_logs.info(f"Begin get request for lab results at {utils.get_time()}")
    if lab_id is None:
        error = utils.create_error(schemas.ErrorTypeEnum.missing_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if not utils.is_valid_lab_id(lab_id):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_lab_id)
        return JSONResponse(status_code=404, 
                            content=error)
    
    query = {"limit","offset",  "start", "end", "patient_id", "status", "urgent"}
    params = request.query_params
    # params can be none here as query params are optional for this service
    if (params and not utils.validate_query(params, query)): 
            error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
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
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_patient_id)
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
    lab_results = await crud.get_lab_results(db, data, lab_id)
    result = []
    for obj in lab_results: 
        analysis = schemas.Analysis(
            request_id=obj.request_id,
            lab_id=obj.lab_id,
            patient_id=obj.patient_id,
            result=obj.result,
            urgent=obj.urgent,
            created_at=obj.created_at.isoformat(timespec='seconds').replace('+00:00','Z'),
            updated_at=obj.updated_at.isoformat(timespec='seconds').replace('+00:00','Z')
        )
        result.append(analysis.dict())
    request_logs.info(f"End of get request for lab results at {utils.get_time()}")
    return JSONResponse(status_code=200, 
                        content=result) 

@resultRouter.get('/labs/results/{lab_id}/summary')
async def get_result_summary(lab_id: str, start: str = Query(None, description="start"), 
                       end: str = Query(None, description="end"), 
                       db:AsyncSession = Depends(get_db), request: Request = None):
    # required params (check id)
    request_logs.info(f"Begin get request for lab summary at {utils.get_time()}")
    if lab_id is None:
        error = utils.create_error(schemas.ErrorTypeEnum.missing_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if not utils.is_valid_lab_id(lab_id): 
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_lab_id)
        return JSONResponse(status_code=404, 
                            content=error)
    # optional params (can be none) if parameters are given, check...
    query = {"start", "end"}
    params = request.query_params
    if (params and not utils.validate_query(params, query)):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
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
    # everything is valid, begin processing request
    data = await crud.get_summary_results(db, lab_id)
    request_logs.info(f"End of get request for lab summary at {utils.get_time()}")
    return JSONResponse(status_code=200, 
                            content=data.dict())


def determine_limit(lim: int):
    if (lim < 0):
        return 0
    if (lim > 1000): 
        return 1000