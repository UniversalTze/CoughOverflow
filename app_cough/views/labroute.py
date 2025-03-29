from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db

labrouter = APIRouter()

@labrouter.get('/labs', response_model=schemas.Labs)
def get_labs(db:Session = Depends(get_db)):
    result = crud.get_lab_ids(db)
    return {"labs": [lab.id for lab in result]}