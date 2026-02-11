from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Visit
from schemas import VisitUpdate, VisitOut

router = APIRouter(prefix="/v1/visits", tags=["visits"])


@router.get("", response_model=list[VisitOut])
def list_visits(uid: str = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Visit)
    if uid:
        q = q.filter(Visit.uid == uid)
    return q.all()


@router.put("/{visit_id}", response_model=VisitOut)
def update_visit(visit_id: int, body: VisitUpdate, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if key == "id":
            continue
        setattr(visit, key, value)
    db.commit()
    db.refresh(visit)
    return visit

