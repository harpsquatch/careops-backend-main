from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Patient, Visit
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


# ─── Chart data (real care scores from visit history) ───


def _compute_care_scores(visits: list, patient: Patient, window: int = 14):
    """
    Compute a daily care score (0-100) over the last 90 days + 14 day forecast.

    Score = weighted sum of three components:
      • Adherence  (50%):  completed / total due visits in rolling window
      • Timeliness (30%):  on-time completions / total completions in window
      • Engagement (20%):  actual frequency vs expected (scheduled_visits/month)

    Returns (labels, values, forecast_values, valid_index).
    """
    today = date.today()
    history_days = 90
    forecast_days = 14
    total_days = history_days + forecast_days

    # Parse visits into structured dicts for fast lookup
    parsed = []
    for v in visits:
        due = None
        comp = None
        try:
            due = date.fromisoformat(v.due_date) if v.due_date else None
        except (ValueError, TypeError):
            pass
        try:
            comp = date.fromisoformat(v.completed_date) if v.completed_date else None
        except (ValueError, TypeError):
            pass
        parsed.append({
            "due": due,
            "comp": comp,
            "status": v.status,   # 1=pending, 2=completed
        })

    expected_per_month = patient.scheduled_visits or 4
    expected_per_window = expected_per_month * window / 30.0

    labels = []
    values = []
    forecast_values = []
    valid_index = history_days - 1  # last historical day

    # EMA smoothing factor
    alpha = 0.25
    smoothed = None

    for i in range(total_days):
        d = today - timedelta(days=history_days - 1 - i)
        labels.append(d.isoformat())

        is_forecast = i >= history_days

        if not is_forecast:
            # ── Historical: compute from real visits ──
            win_start = d - timedelta(days=window - 1)

            # Only count visits with due_date up to today (not future scheduled ones)
            due_in_window = [p for p in parsed if p["due"] and win_start <= p["due"] <= d]
            completed_in_window = [p for p in due_in_window if p["status"] == 2 and p["comp"]]

            total_due = len(due_in_window)
            total_completed = len(completed_in_window)

            # ── Adherence (50%) ──
            if total_due > 0:
                adherence = total_completed / total_due
            else:
                adherence = 1.0  # no visits due = assume stable

            # ── Timeliness (30%) ──
            if total_completed > 0:
                on_time = sum(
                    1 for p in completed_in_window
                    if p["comp"] and p["due"] and p["comp"] <= p["due"]
                )
                timeliness = on_time / total_completed
            else:
                timeliness = 1.0 if total_due == 0 else 0.0

            # ── Engagement (20%) ──
            if expected_per_window > 0:
                engagement = min(1.0, total_completed / expected_per_window)
            else:
                engagement = 1.0

            raw_score = (adherence * 50) + (timeliness * 30) + (engagement * 20)
            raw_score = max(0, min(100, raw_score))

            # EMA smooth
            if smoothed is None:
                smoothed = raw_score
            else:
                smoothed = alpha * raw_score + (1 - alpha) * smoothed

            values.append(round(smoothed, 1))

            # Confidence band — tighter when more data
            if total_due > 0:
                band = max(3, 10 - total_due)
            else:
                band = 8
        else:
            # ── Forecast: hold last score with gentle mean-reversion toward 70 ──
            last_score = smoothed if smoothed is not None else 50
            target = 70  # long-term mean
            reversion = 0.02  # slow pull toward target
            last_score = last_score + (target - last_score) * reversion
            smoothed = last_score
            values.append(round(last_score, 1))

            # Wider confidence band in forecast
            days_ahead = i - history_days + 1
            band = 4 + days_ahead * 0.8

        forecast_values.append({"min": round(band, 1), "max": round(band, 1)})

    return labels, values, forecast_values, valid_index


@router.get("/{patient_id}/chart")
def get_chart(patient_id: int, uid: str = Query(default=None), db: Session = Depends(get_db)):
    """Compute care score timeline from real visit data."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch all visits for this patient
    visits = db.query(Visit).filter(Visit.field_id == patient_id).all()

    labels, values, forecast_values, valid_index = _compute_care_scores(visits, patient)

    return {
        "labels": labels,
        "values": values,
        "forecast_values": forecast_values,
        "valid_index": valid_index,
    }


@router.get("/{patient_id}/summary")
def get_patient_summary(patient_id: int, uid: str = Query(default=None), db: Session = Depends(get_db)):
    """
    Generate an AI-powered patient summary from live data.
    Returns structured insights: status, risks, cadence, next actions, AI-generated insights.
    """
    from agents.summary_agent import run_patient_summary_agent

    return run_patient_summary_agent(patient_id=patient_id, uid=uid, db=db)

