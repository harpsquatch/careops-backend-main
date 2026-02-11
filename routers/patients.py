import math
import random
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Patient
from schemas import PatientCreate, PatientUpdate, PatientOut

router = APIRouter(prefix="/v1/patients", tags=["patients"])


@router.get("", response_model=list[PatientOut])
def list_patients(uid: str = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Patient)
    if uid:
        q = q.filter(Patient.uid == uid)
    return q.all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, uid: str = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Patient).filter(Patient.id == patient_id)
    if uid:
        q = q.filter(Patient.uid == uid)
    patient = q.first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("", response_model=PatientOut)
def create_patient(body: PatientCreate, uid: str = Query(default=None), db: Session = Depends(get_db)):
    patient = Patient(**body.model_dump(), uid=uid or "1")
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, body: PatientUpdate, uid: str = Query(default=None), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}")
def delete_patient(patient_id: int, uid: str = Query(default=None), db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"ok": True}


# ─── Chart data ───

@router.get("/{patient_id}/chart")
def get_chart(patient_id: int, uid: str = Query(default=None)):
    """Generate smoothed care-score timeline for a patient."""
    seed = patient_id * 137
    rng = random.Random(seed)

    labels, values, forecast_values = [], [], []
    from datetime import date, timedelta
    today = date.today()

    score = 40 + rng.random() * 20  # start 40-60
    mean = score

    for i in range(90):
        d = today - timedelta(days=89 - i)
        labels.append(d.isoformat())

        drift = (mean - score) * 0.05
        score += drift + rng.gauss(0, 1.2)
        score = max(5, min(95, score))
        values.append(round(score, 1))

        band = 6 + rng.random() * 4
        forecast_values.append({"min": round(band, 1), "max": round(band, 1)})

    valid_index = len(labels) - 1
    return {
        "labels": labels,
        "values": values,
        "forecast_values": forecast_values,
        "valid_index": valid_index,
    }

