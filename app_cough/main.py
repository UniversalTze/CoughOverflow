from fastapi import FastAPI
from app_cough import healthrouter

app = FastAPI()

app.include_router(healthrouter, prefix="/api/v1")