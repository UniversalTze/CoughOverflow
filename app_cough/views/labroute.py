from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db

labrouter = APIRouter()

@labrouter.get('/labs')
async def get_labs(db:AsyncEngine = Depends(get_db)):
    result = await crud.get_lab_ids(db) # sql alchemy returns for each lab id as a tuple. 
    # labs = [lab[0] for lab in result]
    return result

# Just a test
@labrouter.get('/validlabs')
async def get_labs(db:AsyncEngine = Depends(get_db)):
    result = await crud.get_valid_labs(db)
    #  labs = [lab["id"] for lab in result]
    return result
