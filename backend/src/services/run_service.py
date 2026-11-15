from sqlalchemy import select
from fastapi import HTTPException
from src.models import DirectionRun,DirectionSurvey,Mooring,BearingReading
from src.config.queue import queue
from src.constants.enums import RunStatus
from src.utils.audit import record
from src.utils.serializers import serialize
from src.services.analysis_algorithm import analyze
QUEUE='currents:runs'
def slim(data):
    data=dict(data);result=dict(data.get('result') or {});snapshot=result.pop('input_snapshot',None)
    if snapshot is not None:result['input_snapshot_meta']={'a':len(snapshot.get('a') or []),'b':len(snapshot.get('b') or []),'config':snapshot.get('config')}
    data['result']=result;return data
def listing(db):return [slim(serialize(x)) for x in db.scalars(select(DirectionRun).order_by(DirectionRun.id.desc()))]
def create(db,data,user):
    if not db.get(DirectionSurvey,data.survey_id) or not db.get(Mooring,data.mooring_a_id) or not db.get(Mooring,data.mooring_b_id):raise HTTPException(404,'调查或浮标不存在')
    if db.scalar(select(DirectionRun).where(DirectionRun.name==data.name)):raise HTTPException(409,'研究名称重复')
    row=DirectionRun(**data.model_dump(),created_by=user.id,status=RunStatus.QUEUED);db.add(row);db.flush();record(db,user,'run.queued',row.id);db.commit();queue.rpush(QUEUE,str(row.id));return serialize(row)
def snapshot(db,id,group,offset,limit):
    run=db.get(DirectionRun,id)
    if not run:raise HTTPException(404,'研究不存在')
    if group not in ('a','b'):raise HTTPException(422,'分组须为a或b')
    saved=(run.result or {}).get('input_snapshot') or {};rows=saved.get(group) or []
    return {'total':len(rows),'rows':rows[offset:offset+limit]}
def compute(db,id):
    run=db.get(DirectionRun,id)
    if not run or run.status not in ['queued','running']:return
    run.status=RunStatus.RUNNING;db.commit()
    rows=[]
    for mooring_id in [run.mooring_a_id,run.mooring_b_id]:
        items=db.execute(select(BearingReading.code,BearingReading.bearing,BearingReading.observed_at).where(BearingReading.survey_id==run.survey_id,BearingReading.mooring_id==mooring_id).order_by(BearingReading.code)).all()
        rows.append([{'code':code,'bearing':bearing,'observed_at':observed_at} for code,bearing,observed_at in items])
    run.result=analyze(*rows,{'survey_id':run.survey_id,'mooring_a_id':run.mooring_a_id,'mooring_b_id':run.mooring_b_id,'permutations':run.permutations,'seed':run.seed});run.status=RunStatus.COMPLETED;run.error='';db.commit();return serialize(run)
