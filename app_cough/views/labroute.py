from fastapi import APIRouter

labrouter = APIRouter()

@labrouter.get('/labs')
def get_labs():
    #health logic will come when db and other services are added
    return {[]}