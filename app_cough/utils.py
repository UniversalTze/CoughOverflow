from datetime import datetime, timezone
from starlette.datastructures import QueryParams
from app_cough.models import schemas, crud, get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


LENGTH_PATIENT_ID = 11
VALID_SET = set()
# only is_valid_lab_id needs to be async as it process data from async connection db. (Rest is just pure python logic)

def validate_query(given: QueryParams, required: set):
    params = [arg for arg in given]
    if len(params) > len(required):
        return False # too many parameters supplied
    parameters = set(params)
    if not parameters.issubset(required):  # params are subset of required
        return False
    for key in given: 
        if len(given.getlist(key)) > 1: # Duplicate keys
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
        # Based on code from https://stackoverflow.com/questions/62764701/how-to-validate-that-a-string-is-a-time-in-rfc3339-format
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').tzinfo is not None
    except ValueError as e:
        return False
    
def is_valid_lab_id(lab_id: str): 
    labs = get_valid_lab_set()
    if (lab_id not in labs):
        return False
    return True

def is_valid_date(date: str): 
    date.replace("Z", "+00:00")
    return is_rfc3339(date)

def create_error(incorrect: schemas.ErrorTypeEnum): 
    invalid = schemas.AnalysisPostError(error=incorrect.name, detail=incorrect.value)
    return {"error": invalid.error,
            "detail": invalid.detail}

def determine_status(status: str):
    for enums in schemas.StatusEnum:
        if enums.value == status: 
            return enums
        
def get_time():
    return datetime.now(timezone.utc).isoformat()

def load_valid_lab_set(file_path): 
     with open(file_path, 'r', encoding="utf-8-sig", newline='') as csvfile:
        # Added encoding as csv had some buggy characters 
        for line in csvfile:
            # Process each line manually
            labid = line.strip()
            VALID_SET.add(labid)

def get_valid_lab_set(): 
    return VALID_SET