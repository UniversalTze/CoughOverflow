import subprocess
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app_cough.models.database import get_db
from app_cough.models import dbmodels

RETURN_FROM_ENGINE = {"covid-19": "covid", "healthy": "healthy", "h5n1": "h5n1"}
def worker_image(input: str, output: str, request:str, tmp_loc: str):
    print("worker starting")
    SQLALCHEMY_DATABASE_URL = "postgresql://cough_user:superSecretPassword.23@database:5432/cough"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    status = None
    result = subprocess.run(["./overflowengine", "--input", input, "--output", output], capture_output=True)
    if (result.returncode != 0): 
        message = "failed"
    else: 
        with open(output, "r") as f: 
            message = f.read().strip()

        message = RETURN_FROM_ENGINE.get(message, "failed")
    req = db.query(dbmodels.Request).filter(dbmodels.Request.request_id == request).first()
    req.result = message
    db.commit()
    db.refresh(req)
    db.close()
    