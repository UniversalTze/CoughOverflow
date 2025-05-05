import boto3, os, watchtower, logging
from celery import Celery
from celery.signals import worker_ready
from kombu import Queue
 
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