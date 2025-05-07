import boto3, os, watchtower, logging, tempfile, os
from datetime import datetime, timezone
from celery import Celery
from celery.signals import worker_ready
from kombu import Queue
import subprocess, os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app_cough.models import dbmodels
from functools import lru_cache
 
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

# Buckets was received, thank goodness.
@celery.task
def send_startup_message(msg):
    file_name = f"{msg}_received.txt"
    s3 = boto3.client('s3')
    bucket_name = "coughoverflow-s3-23182020"
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=b"Startup message received"
    )
    print(f"[Startup Message] {msg}")


RETURN_FROM_ENGINE = {"covid-19": "covid", "healthy": "healthy", "h5n1": "h5n1"}
@celery.task(name="do_analysis_normal")
def analyse_image(msg):
    time = datetime.now(timezone.utc).isoformat()
    celery_logger.info(f"Begining analysis at {time} for normal analysis")
    
    saved_img = download_image_S3(msg) # Download image
    tmp_dir = tempfile.gettempdir()

    # DB connection
    celery_logger.info("Establishind Sync DB Connection for normal analysis")
    db = connect_db()

    output = f"{tmp_dir}/{msg}.txt" # output result file
    celery_logger.info("Running engine now for normal analysis")
    result = run_engine(input_path=saved_img, output_path=output)

    message = RETURN_FROM_ENGINE.get(result, "failed")
    time = datetime.now(timezone.utc).isoformat()
    celery_logger.info(f"Updating db with {message} at {time} for normal analysis")
    update_db(message, msg, db)
    celery_logger.info("Analysis completed for normal")

@celery.task(name="do_analysis_urgent")
def analyse_image_urgent(msg):
    time = datetime.now(timezone.utc).isoformat()
    celery_logger.info(f"Begining analysis at {time} for urgent queue")
    
    saved_img = download_image_S3(msg) # Download image
    tmp_dir = tempfile.gettempdir()

    # DB connection
    celery_logger.info("Establishind Sync DB Connection for urgent queue")
    db = connect_db()

    output = f"{tmp_dir}/{msg}.txt" # output result file
    celery_logger.info("Running engine now for urgent queue")
    result = run_engine(input_path=saved_img, output_path=output)

    message = RETURN_FROM_ENGINE.get(result, "failed")
    time = datetime.now(timezone.utc).isoformat()
    celery_logger.info(f"Updating db with {message} at {time} for urgent queue")
    update_db(message, msg, db)
    celery_logger.info("Analysis completed for urgent queue")

def download_image_S3(id: str) -> str:
    celery_logger.info(f"Downloading {id} from bucket")
    s3 = boto3.client('s3')
    bucket_name = "coughoverflow-s3-23182020"
    file_name = f"{id}.jpg"
    tmp_dir = tempfile.gettempdir()
    save_path = f"{tmp_dir}/{id}.jpg"
    s3.download_file(bucket_name, file_name, save_path)

    return save_path

def connect_db() -> Session:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    return db

@lru_cache(maxsize=1)
def get_engine():
    uri = os.getenv("SQLALCHEMY_SYNC_DATABASE_URI")
    if not uri:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set")
    return create_engine(uri)

def run_engine(input_path, output_path) -> str:
    celery_logger.info("Running engine")
    result = subprocess.run(["./overflowengine", "--input", input_path, "--output", output_path], capture_output=True)
    if result.returncode != 0:
        return "failed"
    with open(output_path, "r") as f: #File closes after block
        message = f.read().strip()
        return message
    
def update_db(res: str, req_id: str, db: Session):
    req = db.query(dbmodels.Request).filter(dbmodels.Request.request_id == req_id).first()
    req.result = res
    db.commit()
    db.refresh(req)
    db.close()