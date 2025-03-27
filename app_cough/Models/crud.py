from sqlalchemy.orm import Session
from . import dbmodels, schemas

# Create, Read, Update and Delete Operations with database
def get_labs(db: Session):
    return db.query(dbmodels.Labs).all()