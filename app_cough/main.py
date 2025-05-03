import logging, boto3, watchtower, uuid
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

# Set up logging (next time do it in a module) Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

handler = watchtower.CloudWatchLogHandler(   # Configures watchtower to log to AWS CloudWatch. (currently not working rn)
           log_group_name="coughoverflow-test",
           boto3_client=boto3.client("logs", region_name="us-east-1")
   )


# Custom request logger formatter
class RequestFormatter(logging.Formatter):
    def format(self, record):
        # Custom log structure to include request-related info
        record.msg = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": record.request_id,  # Custom request_id
            "method": record.method,  # HTTP method
            "url": record.url,  # Request URL
            "status_code": record.status_code,  # HTTP Status
        }
        return super().format(record)


# Set up the requests logger
requests_logger = logging.getLogger("requests")
requests_logger.setLevel(logging.INFO)
requests_logger.addHandler(handler)
# handler.setFormatter(RequestFormatter())

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())  # Generate a unique request ID
    method = request.method
    url = str(request.url)
    
    # Log request start
    requests_logger.info("Request Started", extra={
        "request_id": request_id,
        "method": method,
        "url": url
    })
    requests_logger.info(request_id)
    
    response = await call_next(request)
    
    # Log request end
    requests_logger.info("Request Finished", extra={
        "request_id": request_id,
        "method": method,
        "url": url,
        "status_code": response.status_code
    })
    
    return response
################################# Logging
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
