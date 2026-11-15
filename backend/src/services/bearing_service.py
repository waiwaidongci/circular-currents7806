from sqlalchemy import select,func
from fastapi import HTTPException
from src.models import BearingReading,DirectionSurvey,Mooring
from src.constants.limits import MAX_GROUP_SIZE
from src.utils.audit import record
from src.utils.serializers import serialize
def listing(db,survey_id,mooring_id,offset,limit):
    query=select(BearingReading).where(BearingReading.survey_id==survey_id)
    if mooring_id:query=query.where(BearingReading.mooring_id==mooring_id)
    count=db.scalar(select(func.count()).select_from(query.subquery()))
    return {'total':count,'rows':[serialize(x) for x in db.scalars(query.order_by(BearingReading.code).offset(offset).limit(limit))]}
def import_rows(db,data,user):
    if not db.get(DirectionSurvey,data.survey_id) or not db.get(Mooring,data.mooring_id):raise HTTPException(404,'调查或浮标不存在')
    codes=[x.code for x in data.readings]
    if db.scalar(select(BearingReading).where(BearingReading.code.in_(codes))):raise HTTPException(409,'采样编号已存在')
    n=db.scalar(select(func.count()).select_from(BearingReading).where(BearingReading.survey_id==data.survey_id,BearingReading.mooring_id==data.mooring_id))
    if n+len(codes)>MAX_GROUP_SIZE:raise HTTPException(422,f'每期每浮标最多{MAX_GROUP_SIZE}条；已有{n}条，本批{len(codes)}条超出上限')
    db.add_all([BearingReading(survey_id=data.survey_id,mooring_id=data.mooring_id,**x.model_dump()) for x in data.readings]);record(db,user,'bearings.imported',data.survey_id);db.commit();return {'inserted':len(codes)}
