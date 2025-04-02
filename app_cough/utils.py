from datetime import datetime
from starlette.datastructures import QueryParams
from app_cough.models import schemas, crud, get_db
from fastapi import Depends
from sqlalchemy.orm import Session

def validate_query(given: QueryParams, required: set):
    params = [arg for arg in given]
    if len(params) > len(required):
        return False # too many parameters supplied
    parameters = set(params)
    if not parameters.issubset(required):  # params are subset of required
        return False
    for key in given:
        if len(given.getlist(key)) > 1:
            return False
    return True

def validate_body(args: list, required: set):
    if len(args) != len(required):
        return False # too many parameters supplied (should only be one)
    for item in args: 
        if item != 'image':
            return False
    return True

def is_valid_status(value: str) -> bool:
    return value in {status.value for status in schemas.StatusEnum}

def is_rfc3339(date_str: str) -> bool:
    try: 
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').tzinfo is not None
    except ValueError as e:
        return False
    
def is_valid_lab_id(lab_id: str, db:Session):
    labs = crud.get_valid_labs(db) # list of all object items
    ids = set(lab.id for lab in labs)
    if (lab_id not in ids):
        return False
    return True

def is_valid_date(date: str): 
    date.replace("Z", "+00:00")
    return is_rfc3339(date)

def create_error(incorrect: schemas.ErrorTypeEnum): 
    invalid = schemas.AnalysisPostError(error=incorrect.name, detail=incorrect.value)
    return {"error": invalid.error,
            "detail": invalid.detail}