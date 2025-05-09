import boto3, base64, uuid, tempfile, logging, aioboto3, aiofiles
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.params import Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app_cough.models import schemas, crud, dbmodels, database, get_db
from typing import Union
from app_cough import utils

MIN_KB = 4 * 1000
MAX_KB = 150 * 1000

analysisrouter = APIRouter()
request_logs = logging.getLogger("app.requests")

@analysisrouter.post('/analysis', response_model= Union[schemas.AnalysisPost, schemas.AnalysisPostError])
async def create_analysis(patient_id: str = Query(None, description="patient_id"), 
                    lab_id: str = Query(None, description="lab_id"), 
                    urgent: bool = Query(None, description="urgent"),
                    body: dict = Body(None), 
                    db: AsyncSession = Depends(get_db), 
                    request: Request= None): 
    request_logs.info(f"Begin Post request at {utils.get_time()}")
    req_body = {"image"}
    if (body is None):
        error = utils.create_error(schemas.ErrorTypeEnum.no_image)
        return JSONResponse(status_code=400, 
                            content=error)
    given_body = [params for params in body] # check body
    if not utils.validate_body(args=given_body, required=req_body):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
    query_params = request.query_params
    query = {"patient_id", "lab_id", "urgent"}
    if (query_params and not utils.validate_query(query_params, required=query)): # check params provided in query
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if patient_id is None:
        error = utils.create_error(schemas.ErrorTypeEnum.missing_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if (len(patient_id) != utils.LENGTH_PATIENT_ID):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_patient_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if (lab_id is None):
        error = utils.create_error(schemas.ErrorTypeEnum.missing_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if (not utils.is_valid_lab_id(lab_id)):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)

    image  = body["image"]
    try: 
        decoded_img = base64.b64decode(image, validate=True)
    except (base64.binascii.Error, ValueError):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_image_encryption)
        return JSONResponse(status_code=400, 
                            content=error)
    size_img = len(decoded_img)
    if (size_img < MIN_KB or size_img > MAX_KB):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_image_size)
        return JSONResponse(status_code=400, 
                            content=error)
    
    if not decoded_img.startswith(b"\xFF\xD8") or not decoded_img.endswith(b"\xFF\xD9"):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_image_format)
        return JSONResponse(status_code=400, 
                            content=error)
    
    id_req = str(uuid.uuid4())
    request = dbmodels.Request(
        request_id=id_req,
        lab_id = lab_id,
        patient_id=patient_id,
        result=schemas.StatusEnum.PENDING.value,
        urgent=urgent
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    message = schemas.AnalysisPost(
        id=request.request_id,
        created_at=request.created_at.isoformat(timespec='seconds').replace('+00:00','Z'),
        updated_at=request.created_at.isoformat(timespec='seconds').replace('+00:00','Z'),
        status=request.result
    )
    # get the nessary stuff from request before closing connection for fork()
    await db.close()
    request_logs.info(f"{id_req} passed all tests, publish to db")
    # create a temp directory to store these results. 
    tmp_dir = tempfile.gettempdir()
    input_path = f"{tmp_dir}/{id_req}.jpg"
    # write decoded image to .jpeg file
    with open(input_path, "wb") as f:
        f.write(decoded_img)
    
    # add to s3 bucket
    request_logs.info(f"Adding {id_req} .jpg to a bucket")
    async with aioboto3.Session().client("s3") as s3:
        bucket_name = "coughoverflow-s3-23182020"
        s3_key = f"{id_req}.jpg"
        async with aiofiles.open(input_path, "rb") as file_obj:
            await s3.upload_fileobj(file_obj, bucket_name, s3_key)
    
    from app_cough.tasks import analysis 
    if urgent is None or urgent == False: 
        analysis.analyse_image.apply_async(args=[id_req], queue="cough-worker-normal-queue")
    else: 
        analysis.analyse_image_urgent.apply_async(args=[id_req], queue="cough-worker-urgent.fifo")
    request_logs.info(f"Finish Post request for {id_req} at {utils.get_time()}")
    return JSONResponse(status_code=201, content=message.dict())

@analysisrouter.get('/analysis', response_model= schemas.Analysis) 
async def get_request(request_id: str = Query(None, description="request_id"), 
                      db: AsyncSession = Depends(get_db), 
                      request: Request= None):
    request_logs.info(f"Begin Get request at {utils.get_time()}")
    query = {"request_id"}
    query_params = request.query_params 
    if (query_params and not utils.validate_query(query_params, query)):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    if (request_id is None):
        error = utils.create_error(schemas.ErrorTypeEnum.missing_request_id)
        return JSONResponse(status_code=400, 
                            content=error)
    result = await crud.get_requests(db, request_id)
    if result is None:
        return JSONResponse(status_code=404, 
                                content= {
                                    "error": "request id not found",
                                    "detail": "request id does not correspond to any submitted analysis requests"
                                })
    info = schemas.Analysis(
            request_id=result.request_id,
            lab_id=result.lab_id,
            patient_id=result.patient_id,
            result=result.result,
            urgent=result.urgent,
            created_at=result.created_at.isoformat(timespec='seconds').replace('+00:00','Z'),
            updated_at=result.updated_at.isoformat(timespec='seconds').replace('+00:00','Z'),
        )
    request_logs.info(f"Finish get request at {utils.get_time()}")
    return JSONResponse(status_code=200, 
                                content=info.dict())
    
@analysisrouter.put('/analysis') # response_model= Union[schemas.AnalysisPost, schemas.AnalysisUpdateError])
async def update_request(request_id: str = Query(None, description="request_id"), 
                   lab_id: str = Query(None, description="lab_id"), 
                   db: AsyncSession = Depends(get_db), request: Request= None): 
    request_logs.info(f"Begin Put request at {utils.get_time()}")
    query = {"request_id", "lab_id"}
    query_params = request.query_params
    if (query_params and not utils.validate_query(given=query_params, required=query)):
        error = utils.create_error(schemas.ErrorTypeEnum.invalid_query)
        return JSONResponse(status_code=400, 
                            content=error)
    if (lab_id is None): 
        error = utils.create_error(schemas.ErrorTypeEnum.missing_lab_id)
        return JSONResponse(status_code=400, 
                            content=error)
    if (request_id is None):
        error = utils.create_error(schemas.ErrorTypeEnum.missing_request_id)
        return JSONResponse(status_code=400, 
                            content=error)

    if (not utils.is_valid_lab_id(lab_id)):
        error = schemas.AnalysisUpdateError(detail="Invalid lab identifier.")
        return JSONResponse(status_code=400, 
                            content=error.dict())
    req = await crud.get_requests(db, request_id) # returns None or ORM object
    if req is None:
        return JSONResponse(status_code=404, 
                                content= {
                                    "error": "request id not found",
                                    "detail": "request id does not correspond to any submitted analysis requests"
                                })
    # there is a valid result id and lab is valid, need to update the row. 
    req = await crud.update_requests(db, req, lab_id) # refresh in update_request function
    info = schemas.Analysis(request_id=req.request_id,
                lab_id=req.lab_id,
                patient_id=req.patient_id,
                result=req.result,
                urgent=req.urgent,
                created_at=req.created_at.isoformat(timespec='seconds').replace('+00:00','Z'),
                updated_at=req.updated_at.isoformat(timespec='seconds').replace('+00:00','Z'))
    request_logs.info(f"Finish Put request at {utils.get_time()}")
    return JSONResponse(status_code=200, content=info.dict())
