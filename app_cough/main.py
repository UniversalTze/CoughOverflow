import logging, boto3, watchtower, os
import urllib.request # Downloading CSV file 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app_cough import healthrouter, labrouter, analysisrouter,resultRouter
from app_cough import utils
from .models import engine, dbmodels, AsyncSessionLocal, schemas
from celery import Celery
from kombu import Queue

#Command to start app, might need to SH.
# uvicorn app_cough.main:app --port 6400
app = FastAPI()

# Set up logging (next time do it in a module) Logging
logger = logging.getLogger(__name__)
handler = watchtower.CloudWatchLogHandler(   # Configures watchtower to log to AWS CloudWatch. (currently not working rn)
        log_group_name="coughoverflow-test",
        boto3_client=boto3.client("logs", region_name="us-east-1")
)
logging.basicConfig(level=logging.INFO)
logging.getLogger("sqlalchemy.engine").addHandler(handler) #check if this is or a log stream for sql alchemy engine
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
request_logs = logging.getLogger("app.requests")
request_logs.addHandler(handler)
request_logs.setLevel(level=logging.INFO)

# Celery queue
celery_app = Celery("cough-analysis")
celery_app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery_app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND") 
normal = os.environ.get("NORMAL_QUEUE")
urgent = os.environ.get("URGENT_QUEUE")
celery_app.conf.task_queues = [
    Queue(normal),
    Queue(urgent) 
]
celery_app.conf.task_default_queue = normal

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
    # Create list of valid labs
    path, _ =  urllib.request.urlretrieve("https://csse6400.uqcloud.net/resources/labs.csv", "./app_cough/labs.csv")

    utils.load_valid_lab_set(path)
    print(utils.get_valid_lab_set())


app.include_router(healthrouter, prefix="/api/v1")
app.include_router(labrouter, prefix="/api/v1")
app.include_router(analysisrouter, prefix="/api/v1")
app.include_router(resultRouter, prefix="/api/v1")
