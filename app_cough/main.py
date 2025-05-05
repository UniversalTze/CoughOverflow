import logging, boto3, watchtower, uuid, os
import urllib.request # Downloading CSV file 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app_cough import healthrouter, labrouter, analysisrouter,resultRouter
from app_cough import send_startup_message
from .models import engine, seed_labs, dbmodels, AsyncSessionLocal, schemas
from pathlib import Path
from sqlalchemy import select
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

# Celery queue
celery_app = Celery("cough-analysis")
celery_app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery_app.conf.task_queues = [
    Queue("cough-worker-normal"),
    Queue("cough-worker-urgent") 
]
celery_app.conf.task_default_queue = "cough-worker-normal"

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
    # Send a message to the queue
    logger.info("sending message to queue normal")
    send_startup_message.apply_async(
        args=["Startup_complete_normal"], 
        queue="cough-worker-normal"
    )
    logger.info("Sending message to urgent queue")
    send_startup_message.apply_async(
        args=["Startup_complete_urgent"], 
        queue="cough-worker-urgent"
    )

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
