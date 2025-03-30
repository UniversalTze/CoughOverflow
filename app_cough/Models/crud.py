from sqlalchemy.orm import Session
from . import dbmodels, schemas

# Create, Read, Update and Delete Operations with database
def get_valid_labs(db: Session):
    return db.query(dbmodels.Labs).all()

def get_lab_ids(db: Session):
    return db.query(dbmodels.Request.lab_id).distinct().all()

def get_requests(db:Session, request: str): #should only be one entry of req id as primary key
    return db.query(dbmodels.Request).filter(dbmodels.Request.request_id == request).first()

def update_requests(db: Session, requestObj, toUpdate: dict):
    for key, value in toUpdate.items():
        setattr(requestObj, key, value)
    db.commit()
    db.refresh(requestObj)
    return requestObj

