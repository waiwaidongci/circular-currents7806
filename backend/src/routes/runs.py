from src.constants.enums import Role
from fastapi import APIRouter,Depends,HTTPException,Query
from src.config.database import session
from src.middlewares.auth import require
from src.schemas.run import RunInput
from src.controllers.run_controller import listing,create,snapshot
from src.models import DirectionRun
from src.utils.serializers import serialize
router=APIRouter(prefix='/runs')
@router.get('')
def index(db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return listing(db)
@router.get('/{id}')
def detail(id:int,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):
    run=db.get(DirectionRun,id)
    if not run:raise HTTPException(404,'研究不存在')
    return serialize(run)
@router.get('/{id}/snapshot')
def input_snapshot(id:int,group:str='a',offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=1000),db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return snapshot(db,id,group,offset,limit)
@router.post('',status_code=202)
def add(data:RunInput,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST))):return create(db,data,u)
