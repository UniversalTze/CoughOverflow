from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db
from app_cough import utils

labrouter = APIRouter()

@labrouter.get('/labs')
async def get_labs(db:AsyncSession = Depends(get_db)):
    result = await crud.get_lab_ids(db) # sql alchemy returns for each lab id as a tuple. 
    # labs = [lab[0] for lab in result]
    return result

# Just a test
@labrouter.get('/validlabs')
async def get_labs(db:AsyncSession = Depends(get_db)):
    result = utils.get_valid_lab_set()
    list_res = list(result)
    #  labs = [lab["id"] for lab in result]
    return list_res
