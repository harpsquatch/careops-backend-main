from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Worker
from schemas import WorkerCreate, WorkerUpdate, WorkerOut

router = APIRouter(prefix="/v1/workers", tags=["workers"])


@router.get("", response_model=list[WorkerOut])
def list_workers(uid: str = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Worker)
    if uid:
        q = q.filter(Worker.account_uid == uid)
    return q.all()


@router.post("", response_model=WorkerOut)
def create_worker(body: WorkerCreate, uid: str = Query(default=None), db: Session = Depends(get_db)):
    worker = Worker(
        uid=str(db.query(Worker).count() + 100),
        account_uid=uid or "1",
        email=body.email,
        full_name=body.email.split("@")[0].replace(".", " ").title(),
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


@router.put("/{worker_uid}", response_model=WorkerOut)
def update_worker(worker_uid: str, body: WorkerUpdate, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.uid == body.uid).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if key == "uid":
            continue
        setattr(worker, key, value)
    db.commit()
    db.refresh(worker)
    return worker

