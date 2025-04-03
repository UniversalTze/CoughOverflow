from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db

labrouter = APIRouter()

@labrouter.get('/labs')
def get_labs(db:Session = Depends(get_db)):
    result = crud.get_lab_ids(db) # sql alchemy returns each lab as a tuple. 
    labs = [lab[0] for lab in result]
    return labs