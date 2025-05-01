from sqlalchemy.ext.asyncio import AsyncSession
from . import dbmodels, schemas
from app_cough import utils
from datetime import datetime, timezone
from sqlalchemy import select, func

# Create, Read, Update and Delete Operations with database
START_DATE =  "start_date"
END_DATE = "end_date"
STATUS = "status"
URGENT = "urgent"
PATIENT = "patient_id"
LAB = "lab"
LIMIT = "limit"
OFFSET = "offset"

async def get_single_lab(db: AsyncSession):
    result = await db.execute(select(dbmodels.Labs).limit(1))
    return result  # If this line runs, DB is alive
    #return db.query(dbmodels.Labs).first()

async def get_valid_labs(db: AsyncSession):
    result = await db.execute(select(dbmodels.Labs.id))
    return result.scalars().all()

async def get_lab_ids(db: AsyncSession):
    #result = await db.execute(dbmodels.Request.lab_id).distinct().all()
    stmt = select(dbmodels.Request.lab_id).distinct()
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_requests(db:AsyncSession, request: str): #should only be one entry of req id as primary key
    stmt = select(dbmodels.Request).filter(dbmodels.Request.request_id == request)
    result = await db.execute(stmt)
    return result.scalars().one_or_none()

async def get_patient_id(db: AsyncSession, patient:str):
    stmt = select(dbmodels.Request).filter(dbmodels.Request.patient_id == patient).limit(1)
    result = await db.execute(stmt)
    return result.scalars().one_or_none()

async def get_patient_results(db: AsyncSession, required_param: str, optional_params: dict):
    query = select(dbmodels.Request).filter(dbmodels.Request.patient_id == required_param)
    # query = db.query(dbmodels.Request).filter(dbmodels.Request.patient_id == required_param)

    if (optional_params[START_DATE] is not None): 
        query = query.filter(dbmodels.Request.created_at >= optional_params[START_DATE])

    if (optional_params[END_DATE] is not None): 
        query = query.filter(dbmodels.Request.created_at <= optional_params[END_DATE])

    if (optional_params[STATUS] is not None):
        stat = utils.determine_status(optional_params[STATUS])
        query = query.filter(dbmodels.Request.result == stat.value)

    if (optional_params[URGENT] is not None):
        query = query.filter(dbmodels.Request.urgent == optional_params[URGENT])
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_lab_results(db: AsyncSession, params: dict, required:str):
    #query = db.query(dbmodels.Request).filter(dbmodels.Request.lab_id == required)
    query = select(dbmodels.Request).filter(dbmodels.Request.lab_id == required)
    query = query.filter(dbmodels.Request.created_at > params[START_DATE]) if params[START_DATE] != None else query
    query = query.filter(dbmodels.Request.created_at <= params[END_DATE]) if params[END_DATE] != None else query
    query = query.filter(dbmodels.Request.patient_id == params[PATIENT]) if params[PATIENT] != None else query
    query = query.filter(dbmodels.Request.result == params[STATUS]) if params[STATUS] != None else query
    query = query.filter(dbmodels.Request.urgent == params[URGENT]) if params[URGENT] != None else query
    # Add offset and limit
    query = query.offset(params[OFFSET]).limit(params[LIMIT])
    result = await db.execute(query)
    return result.scalars().all()

async def get_summary_results(db: AsyncSession, required: str): 
    #base statement (Select * FROM Request where x.labid = required)
    base = select(dbmodels.Request).filter(dbmodels.Request.lab_id == required)
    sub = base.subquery() # subquery
    # base.subquery() makes a subquery table from select statement written in base. 
    # sub.c now relates to the rows returned from subquery (filtering on id)
    # and expose all columns of Request to be used in further filters. (Columns that are selectable)
    pending_stmt = select(func.count()).select_from(sub).filter(sub.c.result == schemas.StatusEnum.PENDING.value)
    covid_stmt   = select(func.count()).select_from(sub).filter(sub.c.result == schemas.StatusEnum.COVID.value)
    h5n1_stmt    = select(func.count()).select_from(sub).filter(sub.c.result == schemas.StatusEnum.H5N1.value)
    healthy_stmt = select(func.count()).select_from(sub).filter(sub.c.result == schemas.StatusEnum.HEALTHY.value)
    failed_stmt  = select(func.count()).select_from(sub).filter(sub.c.result == schemas.StatusEnum.FAILED.value)
    urgent_stmt  = select(func.count()).select_from(sub).filter(sub.c.urgent == True)

    # run all counts concurrently
    pending = (await db.execute(pending_stmt)).scalar()
    covid   = (await db.execute(covid_stmt)).scalar()
    h5n1    = (await db.execute(h5n1_stmt)).scalar()
    healthy = (await db.execute(healthy_stmt)).scalar()
    failed  = (await db.execute(failed_stmt)).scalar()
    urgent  = (await db.execute(urgent_stmt)).scalar()
    requested_time = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    result = schemas.ResultSummary(lab_id=required, 
                                   pending=pending,
                                   covid=covid,
                                   h5n1=h5n1,
                                   healthy=healthy,
                                   failed=failed,
                                   urgent=urgent,
                                   generated_at=requested_time)
    return result

async def update_requests(db: AsyncSession, requestobj: dbmodels.Request, lab_id: str):
    requestobj.lab_id = lab_id
    requestobj.updated_at = datetime.now(timezone.utc) # updates it no matter what
    await db.commit()
    await db.refresh(requestobj)
    return requestobj

