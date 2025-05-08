import boto3, os, watchtower, logging, tempfile, os, aioboto3, asyncio, aiofiles
from datetime import datetime, timezone
from celery import Celery
from celery.signals import worker_ready
from kombu import Queue
import subprocess, os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from app_cough.models import dbmodels
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
 
# Basic Python logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

celery = Celery("cough-analysis")
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND") 
celery.conf.task_queues = [
    Queue("cough-worker-normal"),
    Queue("cough-worker-urgent") 
]
celery.conf.task_default_queue = "cough-worker-normal"
# celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND") 
celery.conf.task_track_started = True

# Create CloudWatch log handler
cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group_name='/coughoverflowengine/coughlogs',  # Same as awslogs-group in ECS config
    boto3_client=boto3.client("logs", region_name="us-east-1"),
)

cloudwatch_handler.setLevel(logging.INFO)
logger.addHandler(cloudwatch_handler)

celery_logger = logging.getLogger("celery")
celery_logger.addHandler(cloudwatch_handler)


@worker_ready.connect
def at_startup(sender, **kwargs): 
    celery_logger.info("Celery worker is ready to perform actions.")

@celery.task(name="do_analysis_normal")
def analyse_image(msg):
    time = datetime.now(timezone.utc)
    celery_logger.info(f"Beginning normal analysis at {time}")
    normal = asyncio.new_event_loop()
    asyncio.set_event_loop(normal)
    try: 
        return normal.run_until_complete(analyse_image_task(msg))
    finally:
        normal.close()

@celery.task(name="do_analysis_urgent")
def analyse_image_urgent(msg):
    time = datetime.now(timezone.utc)
    celery_logger.info(f"Beginning urgent analysis at {time}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: 
        return loop.run_until_complete(analyse_image_task(msg))
    finally:
        loop.close()


async def connect_db() -> AsyncSession:
    engine = get_async_engine()
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    return async_session()

def get_async_engine():
    uri = os.getenv("SQLALCHEMY_DATABASE_URI")
    if not uri:
        raise RuntimeError("SQLALCHEMY_ASYNC_DATABASE_URI is not set")
    return create_async_engine(uri, echo=False, future=True, pool_size=2, max_overflow=0)
    
async def update_db_async(res: str, req_id: str, db: AsyncSession):
    result = await db.execute(
        select(dbmodels.Request).where(dbmodels.Request.request_id == req_id)
    )
    req = result.scalar_one_or_none()
    if req:
        req.result = res
        await db.commit()
        await db.refresh(req)

async def download_image_s3_async(id: str) -> str:
    bucket_name = "coughoverflow-s3-23182020"
    file_name = f"{id}.jpg"
    tmp_dir = tempfile.gettempdir()
    save_path = f"{tmp_dir}/{id}.jpg"
    session = aioboto3.Session()
    async with session.client("s3") as s3:
        async with aiofiles.open(save_path, "wb") as f:
            await s3.download_fileobj(bucket_name, file_name, f)

    return save_path

def run_engine(input_path, output_path) -> str:
    celery_logger.info("Running engine")
    result = subprocess.run(["./overflowengine", "--input", input_path, "--output", output_path], capture_output=True)
    if result.returncode != 0:
        return "failed"
    with open(output_path, "r") as f: #File closes after block
        message = f.read().strip()
        return message

RETURN_FROM_ENGINE = {"covid-19": "covid", "healthy": "healthy", "h5n1": "h5n1"}  
async def analyse_image_task(id: str):
    loop = asyncio.get_running_loop()
    saved_image = await (download_image_s3_async(id))  # Download image from S3
    tmp_dir = tempfile.gettempdir()
    output = f"{tmp_dir}/{id}.txt" # output result file 

    result = await loop.run_in_executor(None, run_engine, saved_image, output)
    message = RETURN_FROM_ENGINE.get(result, "failed")
    db = await connect_db()
    try: 
        await update_db_async(res=message, req_id=id, db=db)
    finally: 
        await db.close()
    time = datetime.now(timezone.utc)
    celery_logger.info(f"End of analysis for {id} at {time}")
