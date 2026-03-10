from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Patient, Visit


def tool_get_patient(db: Session, patient_id: int, uid: Optional[str]) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if uid and patient.uid != uid:
        raise HTTPException(status_code=403, detail="Access denied")
    return patient


def tool_get_visits(db: Session, patient_id: int) -> List[Visit]:
    return db.query(Visit).filter(Visit.field_id == patient_id).all()


def tool_parse_visits(visits: List[Visit]) -> List[Dict[str, Any]]:
    parsed_visits: List[Dict[str, Any]] = []
    for visit in visits:
        due = None
        completed = None
        try:
            due = date.fromisoformat(visit.due_date) if visit.due_date else None
        except (ValueError, TypeError):
            pass
        try:
            completed = date.fromisoformat(visit.completed_date) if visit.completed_date else None
        except (ValueError, TypeError):
            pass
        parsed_visits.append(
            {
                "id": visit.id,
                "due": due,
                "comp": completed,
                "status": visit.status,
                "text": visit.text or "",
            }
        )
    return parsed_visits


def tool_compute_metrics(patient: Patient, parsed_visits: List[Dict[str, Any]]) -> Dict[str, Any]:
    today = date.today()
    last_30_days = today - timedelta(days=30)

    completed_visits = [visit for visit in parsed_visits if visit["status"] == 2 and visit["comp"]]
    pending_visits = [visit for visit in parsed_visits if visit["status"] == 1 and visit["due"]]
    overdue_visits = [visit for visit in pending_visits if visit["due"] and visit["due"] < today]
    upcoming_visits = [visit for visit in pending_visits if visit["due"] and visit["due"] >= today]

    recent_completed = [visit for visit in completed_visits if visit["comp"] and visit["comp"] >= last_30_days]
    recent_due = [visit for visit in parsed_visits if visit["due"] and visit["due"] >= last_30_days]

    adherence_30d = 0.0
    if recent_due:
        completed_in_window = len([visit for visit in recent_completed if visit["due"] and visit["due"] >= last_30_days])
        adherence_30d = (completed_in_window / len(recent_due)) * 100

    next_visit = None
    if upcoming_visits:
        next_visit = min(upcoming_visits, key=lambda visit: visit["due"] if visit["due"] else date.max)

    expected_per_month = patient.scheduled_visits or 4
    cadence = f"{expected_per_month} visits/month expected"
    if recent_due:
        first_due = min(visit["due"] for visit in recent_due if visit["due"])
        actual_per_month = len(recent_due) * (30 / max(1, (today - first_due).days))
        if actual_per_month < expected_per_month * 0.8:
            cadence += f" (currently {actual_per_month:.1f}/month)"

    return {
        "adherence_30d": round(adherence_30d, 1),
        "total_visits": len(parsed_visits),
        "completed_count": len(completed_visits),
        "pending_count": len(pending_visits),
        "overdue_count": len(overdue_visits),
        "upcoming_count": len(upcoming_visits),
        "expected_per_month": expected_per_month,
        "cadence": cadence,
        "next_visit": next_visit,
    }


def tool_classify_risks(patient: Patient, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    risks: List[Dict[str, str]] = []

    if metrics["overdue_count"] > 0:
        risks.append(
            {
                "level": "high" if metrics["overdue_count"] >= 3 else "medium",
                "message": f"{metrics['overdue_count']} overdue visit{'s' if metrics['overdue_count'] > 1 else ''}",
            }
        )
    if metrics["adherence_30d"] < 70 and metrics["pending_count"] + metrics["completed_count"] > 0:
        risks.append(
            {
                "level": "medium",
                "message": f"Low adherence: {metrics['adherence_30d']:.0f}% in last 30 days",
            }
        )
    if not patient.active:
        risks.append({"level": "info", "message": "Patient is currently discharged"})

    return risks


def tool_status_summary(patient: Patient, metrics: Dict[str, Any]) -> str:
    if not patient.active:
        return "Discharged"
    if metrics["overdue_count"] >= 3:
        return "Needs immediate attention"
    if metrics["overdue_count"] > 0:
        return "Behind schedule"
    if metrics["adherence_30d"] >= 90:
        return "On track"
    return "Active care"


def tool_propose_actions(metrics: Dict[str, Any]) -> List[str]:
    actions: List[str] = []
    next_visit = metrics.get("next_visit")
    if next_visit and next_visit.get("due"):
        days_until = (next_visit["due"] - date.today()).days
        if days_until <= 3:
            actions.append(f"Next visit due in {days_until} day{'s' if days_until != 1 else ''}")
    if metrics["overdue_count"] > 0:
        actions.append(f"Reschedule {metrics['overdue_count']} overdue visit{'s' if metrics['overdue_count'] > 1 else ''}")
    if not actions:
        actions.append("No immediate actions required")
    return actions

