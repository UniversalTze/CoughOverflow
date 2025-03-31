import os
import psycopg2
import logging
import urllib.request # Downloading CSV file 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app_cough import healthrouter, labrouter, analysisrouter
from .models import engine, seed_labs, Base, dbmodels, SessionLocal, schemas

#Command to start app, might need to SH.
# uvicorn app_cough.main:app --port 6400
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    # Log the error with details
    logger.error(f"Unexpected error occurred: {exc}")
    
    # Return a graceful JSON response with a 500 status code
    return JSONResponse(
        status_code=500,
        content={
            "error": schemas.ErrorTypeEnum.unknown_error.name,
            "message": schemas.ErrorTypeEnum.value,
            "details": str(exc) 
            # Optional: Include the exception message in the response for debugging purposes
        }
    )

@app.on_event("startup")
def on_startup():
    dbmodels.Base.metadata.create_all(bind=engine)
    
    path, _ =  urllib.request.urlretrieve("https://csse6400.uqcloud.net/resources/labs.csv", "./app_cough/labs.csv")

    db = SessionLocal()
    if db.query(dbmodels.Labs).count() == 0:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of main.py
        file_path = os.path.join(base_dir, "labs.csv")  # Correct file path
        seed_labs(file_path)
    
app.include_router(healthrouter, prefix="/api/v1")
app.include_router(labrouter, prefix="/api/v1")
app.include_router(analysisrouter, prefix="/api/v1")
