import boto3, os, watchtower, logging, tempfile, os
from celery import Celery
from celery.signals import worker_ready
from kombu import Queue
import subprocess, os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app_cough.models import dbmodels
 
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
@celery.task(name="do_analysis")
def analyse_image(msg):
    celery_logger.info("Begining analysis")
    
    celery_logger.info(f"Downloading {msg} from bucket")
    s3 = boto3.client('s3')
    bucket_name = "coughoverflow-s3-23182020"
    file_name = f"{msg}.jpg"
    tmp_dir = tempfile.gettempdir()
    save_path = f"{tmp_dir}/{msg}.jpg"
    s3.download_file(bucket_name, file_name, save_path)

    # DB connection
    celery_logger.info("Establishind Sync DB Connection")
    SQLALCHEMY_DATABASE_URI_VAL = os.getenv("SQLALCHEMY_SYNC_DATABASE_URI")
    if not SQLALCHEMY_DATABASE_URI_VAL:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set in environment...")

    engine = create_engine(SQLALCHEMY_DATABASE_URI_VAL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    output = f"{tmp_dir}/{msg}.txt" # output result file
    celery_logger.info("Running engine now")
    result = subprocess.run(["./overflowengine", "--input", save_path, "--output", output], capture_output=True)

    if (result.returncode != 0): 
        message = "failed"
    else: 
        with open(output, "r") as f: 
            message = f.read().strip()

        message = RETURN_FROM_ENGINE.get(message, "failed")
    celery_logger.info(f"Updating db with {message}")
    req = db.query(dbmodels.Request).filter(dbmodels.Request.request_id == msg).first()
    req.result = message
    db.commit()
    db.refresh(req)
    db.close()
    celery_logger.info("Analysis completed")