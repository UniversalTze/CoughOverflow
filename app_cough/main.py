import psycopg2
import logging
import urllib.request # Downloading CSV file 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app_cough import healthrouter, labrouter, analysisrouter,resultRouter
from .models import engine, seed_labs, dbmodels, AsyncSessionLocal, schemas
from pathlib import Path
from sqlalchemy import select

#Command to start app, might need to SH.
# uvicorn app_cough.main:app --port 6400
app = FastAPI()

# Set up logging (next time do it in a module)
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
            "details": str(exc) 
            # Optional: Include the exception message in the response for debugging purposes
        }
    )

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(dbmodels.Base.metadata.create_all)
    
    path, _ =  urllib.request.urlretrieve("https://csse6400.uqcloud.net/resources/labs.csv", "./app_cough/labs.csv")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(dbmodels.Labs))
        labs_in_db = res.scalars().first()

        if labs_in_db is None: # valid labs has not been added yet
            base_dir = Path(__file__).resolve().parent  # Directory of main.py
            file_path = str(base_dir / "labs.csv")
            await seed_labs(file_path, db=db)
    
app.include_router(healthrouter, prefix="/api/v1")
app.include_router(labrouter, prefix="/api/v1")
app.include_router(analysisrouter, prefix="/api/v1")
app.include_router(resultRouter, prefix="/api/v1")
