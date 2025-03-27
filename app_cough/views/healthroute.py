from fastapi import APIRouter

healthrouter = APIRouter()

@healthrouter.get('/health')
def get_health():
    #health logic will come when db and other services are added
    return {"status": "ok"}