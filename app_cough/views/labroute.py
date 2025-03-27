from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db

labrouter = APIRouter()

@labrouter.get('/labs', response_model=schemas.Labs)
def get_labs(db:Session = Depends(get_db)):
    #health logic will come when db and other services are added
    # All interactions with db must have await.
    result = db.execute(select(dbmodels.Labs))
    # result = await crud.get_labs(db)
    return result