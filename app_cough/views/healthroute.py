import logging
from fastapi import APIRouter, Depends
from app_cough.models import crud, get_db
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from app_cough import utils

healthrouter = APIRouter()
request_logs = logging.getLogger("app.requests")

@healthrouter.get('/health')
async def get_health(db: Session = Depends(get_db)):
    #health logic will come when db and other services are added

    db_healthy = await check_db_health(db)
        
    # Overall health depends only on the database and any additional services. 
    overall_healthy = db_healthy # and for more and more services
    response = { 
        "healthy": overall_healthy,
        "dependencies": [
            {"name": "database", "health": db_healthy}
        ]
    }
    if overall_healthy:
        request_logs.info(f"Service healthy at {utils.get_time()}")
        return JSONResponse(status_code=200, content=response)
    else: 
        return JSONResponse(status_code=503, content=response)

async def check_db_health(db: Session):
    res = await crud.get_single_lab(db)
    return res is not None

