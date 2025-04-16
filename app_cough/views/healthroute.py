from fastapi import APIRouter, Depends
from ..models import crud
from ..models.database import get_db
# from app_cough.models import crud, get_db
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

healthrouter = APIRouter()

@healthrouter.get('/health')
def get_health(db: Session = Depends(get_db)):
    #health logic will come when db and other services are added

    db_healthy = check_db_health(db)
        
    # Overall health depends only on the database and any additional services. 
    overall_healthy = db_healthy # and for more and more services
    response = { 
        "healthy": overall_healthy,
        "dependencies": [
            {"name": "database", "health": db_healthy}
        ]
    }
    if overall_healthy:
        return JSONResponse(status_code=200, content=response)
    else: 
        return JSONResponse(status_code=503, content=response)

def check_db_health(db: Session):
    res = crud.get_single_lab(db)
    return res is not None

