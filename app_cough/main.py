import os
import psycopg2
from fastapi import FastAPI
from app_cough import healthrouter, labrouter
from .models import engine, seed_labs, Base, dbmodels

app = FastAPI()

@app.on_event("startup")
def on_startup():
    dbmodels.Base.metadata.create_all(bind=engine)

    base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of main.py
    file_path = os.path.join(base_dir, "labs.csv")  # Correct file path
    #seed_labs(file_path)

app.include_router(healthrouter, prefix="/api/v1")
app.include_router(labrouter, prefix="/api/v1")
