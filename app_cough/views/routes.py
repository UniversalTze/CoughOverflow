from fastapi import APIRouter

router = APIRouter()

@router.get('/health')
def get_health():
    #health logic will come when db and other services are added
    return {"status": "ok"}