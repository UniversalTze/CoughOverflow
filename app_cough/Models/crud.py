from sqlalchemy.orm import Session
from . import dbmodels, schemas

# Create, Read, Update and Delete Operations with database
def get_valid_labs(db: Session):
    return db.query(dbmodels.Labs).all()

def get_lab_ids(db: Session):
    return db.query(dbmodels.Request.lab_id).distinct().all()

def get_requests(db:Session, request: str):
    return db.query(dbmodels.Request).filter(dbmodels.Request.request_id == request).first()