from sqlalchemy.orm import Session
from . import dbmodels, schemas
from app_cough import utils
from datetime import datetime, timezone

# Create, Read, Update and Delete Operations with database
START_DATE =  "start_date"
END_DATE = "end_date"
STATUS = "status"
URGENT = "urgent"
PATIENT = "patient_ids"
LAB = "lab"
LIMIT = "limit"
OFFSET = "offset"


def get_single_lab(db: Session): 
    return db.query(dbmodels.Labs).first()

def get_valid_labs(db: Session):
    return db.query(dbmodels.Labs).all()

def get_lab_ids(db: Session):
    return db.query(dbmodels.Request.lab_id).distinct().all()

def get_requests(db:Session, request: str): #should only be one entry of req id as primary key
    return db.query(dbmodels.Request).filter(dbmodels.Request.request_id == request).first()

def get_patient_id(db: Session, patient:str):
    return db.query(dbmodels.Request).filter(dbmodels.Request.patient_id == patient).first()

def get_patient_results(db: Session, required_param: str, optional_params: dict):
    query = db.query(dbmodels.Request).filter(dbmodels.Request.patient_id == required_param)

    if (optional_params[START_DATE] is not None): 
        query = query.filter(dbmodels.Request.created_at >= optional_params[START_DATE])

    if (optional_params[END_DATE] is not None): 
        query = query.filter(dbmodels.Request.created_at <= optional_params[END_DATE])

    if (optional_params[STATUS] is not None):
        stat = utils.determine_status(optional_params[STATUS])
        query = query.filter(dbmodels.Request.result == stat.value)

    if (optional_params[URGENT] is not None):
        query = query.filter(dbmodels.Request.urgent == optional_params[URGENT])

    return query.all() # For now.

def get_lab_results(db: Session, params: dict, required:str):
    query = db.query(dbmodels.Request).filter(dbmodels.Request.lab_id == required)
    query = query.filter(dbmodels.Request.created_at > params[START_DATE]) if START_DATE in params else query
    query = query.filter(dbmodels.Request.created_at <= params[END_DATE]) if END_DATE in params else query
    query = query.filter(dbmodels.Request.patient_id == params[PATIENT]) if PATIENT in params else query
    query = query.filter(dbmodels.Request.result == params[STATUS]) if STATUS in params else query
    query = query.filter(dbmodels.Request.urgent == params[URGENT]) if URGENT in params else query
    return query.offset(params[OFFSET]).limit(params[LIMIT]).all()

def get_summary_results(db: Session, required: str): 
    query = db.query(dbmodels.Request).filter(dbmodels.Request.lab_id == required)
    # build the counts from here (build the schema in here
    # pending
    pending = query.filter(dbmodels.Request.result == schemas.StatusEnum.PENDING.value).count()
    covid = query.filter(dbmodels.Request.result == schemas.StatusEnum.COVID.value).count()
    h5n1 = query.filter(dbmodels.Request.result == schemas.StatusEnum.H5N1.value).count()
    healthy = query.filter(dbmodels.Request.result == schemas.StatusEnum.HEALTHY.value).count()
    failed = query.filter(dbmodels.Request.result == schemas.StatusEnum.FAILED.value).count()
    urgent = query.filter(dbmodels.Request.urgent == True).count()
    requested_time = datetime.now(timezone.utc).isoformat(timespec='seconds').replace("+00:00", "Z")
    print(datetime.now(timezone.utc))
    print(f"Requested time {requested_time}")
    result = schemas.ResultSummary(lab_id=required, 
                                   pending=pending,
                                   covid=covid,
                                   h5n1=h5n1,
                                   healthy=healthy,
                                   failed=failed,
                                   urgent=urgent,
                                   generated_at=requested_time)
    return result

def update_requests(db: Session, requestObj, toUpdate: dict):
    for key, value in toUpdate.items():
        setattr(requestObj, key, value)
    db.commit()
    db.refresh(requestObj)
    return requestObj

