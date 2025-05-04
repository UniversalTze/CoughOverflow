import boto3, os, watchtower, logging
from celery import Celery
from celery.signals import worker_ready
 
# Basic Python logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

celery = Celery("cough-analysis")
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
# celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND") 
celery.conf.task_default_queue = "cough-worker"

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