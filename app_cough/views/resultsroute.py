from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.params import Query
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db
from datetime import datetime

resultRouter = APIRouter()

@resultRouter.get('/patients/results') #response_model = schemas.ResultPatient)
def get_patient_results(patient_id: str = Query(None, description="patient_id"),
                        start: str = Query(None, description="start"),
                        end: str = Query(None, description="end"),
                        status: str = Query(None, description="status"),
                        urgent: bool = Query(None, description="urgent"),
                        db:Session = Depends(get_db)):
    # filters are additive, if none, they should not be applied.
    if patient_id is None:
        error = {"error": "Invalid query parameters",
                "detail": "patient id must be supplied using when using this method"}
        return JSONResponse(status_code=400, 
                            content=error)
    # check valid status 
    if status is not None and not is_valid_status(status):
        print(status)
        error = {"error": "Invalid query parameters",
                "detail": "status must be one of 'pending', 'covid', 'h5n1, 'healthy', 'failed'"}
        return JSONResponse(status_code=400, 
                            content=error)

    if start is not None:
        start.replace("Z", "+00:00")
        if not is_rfc3339(start):
            error = {"error": "Invalid query parameters", 
                     "detail": "start date must be of rfc3339 format "}
            return JSONResponse(status_code=400, 
                            content=error)
        else:
            start = datetime.fromisoformat(start)
    
    if end is not None:
        end.replace("Z", "+00:00")
        if not is_rfc3339(end):
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
    print(len(res))
    for obj in res: 
        print("HERE2")
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

def is_valid_status(value: str) -> bool:
    return value in {status.value for status in schemas.StatusEnum}

def is_rfc3339(date_str: str) -> bool:
    try: 
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').tzinfo is not None
    except ValueError as e:
        return False


    