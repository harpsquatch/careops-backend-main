from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from .llm import generate_patient_summary
from .schema import AgentStepTrace, AgentTrace, PatientSummaryOutput
from .tools import (
    tool_classify_risks,
    tool_compute_metrics,
    tool_get_patient,
    tool_get_visits,
    tool_parse_visits,
    tool_propose_actions,
    tool_status_summary,
)


def run_patient_summary_agent(patient_id: int, uid: Optional[str], db: Session) -> Dict[str, Any]:
    trace_steps = []
    trace_id = str(uuid4())
    fallback_used = False

    try:
        patient = tool_get_patient(db, patient_id, uid)
        trace_steps.append(AgentStepTrace(step="get_patient", status="ok", detail="Patient loaded"))

        visits = tool_get_visits(db, patient_id)
        trace_steps.append(AgentStepTrace(step="get_visits", status="ok", detail=f"{len(visits)} visits loaded"))

        parsed_visits = tool_parse_visits(visits)
        trace_steps.append(AgentStepTrace(step="parse_visits", status="ok", detail="Visits parsed"))

        metrics = tool_compute_metrics(patient, parsed_visits)
        trace_steps.append(AgentStepTrace(step="compute_metrics", status="ok", detail="Metrics computed"))

        risks = tool_classify_risks(patient, metrics)
        status_summary = tool_status_summary(patient, metrics)
        actions = tool_propose_actions(metrics)
        trace_steps.append(AgentStepTrace(step="classify_and_plan", status="ok", detail="Risks/actions prepared"))

        patient_data = {
            "name": patient.field_name,
            "care_level": patient.acres or "Unknown",
            "description": patient.description or "",
            "active": patient.active,
        }

        visit_metrics = {
            "adherence_30d": metrics["adherence_30d"],
            "total_visits": metrics["total_visits"],
            "completed_count": metrics["completed_count"],
            "pending_count": metrics["pending_count"],
            "overdue_count": metrics["overdue_count"],
            "upcoming_count": metrics["upcoming_count"],
            "cadence": metrics["cadence"],
            "status_summary": status_summary,
            "actions": actions,
            "next_visit_date": metrics["next_visit"]["due"].isoformat() if metrics.get("next_visit") and metrics["next_visit"].get("due") else None,
        }

        ai_summary = generate_patient_summary(patient_data, visit_metrics, risks)
        trace_steps.append(AgentStepTrace(step="llm_summary", status="ok", detail="LLM summary generated"))

        next_visit = metrics.get("next_visit")
        result = {
            "patient_id": patient_id,
            "patient_name": patient.field_name,
            "status_summary": ai_summary.get("status_summary", status_summary),
            "care_level": patient.acres or "Unknown",
            "description": patient.description or "",
            "adherence_30d": metrics["adherence_30d"],
            "total_visits": metrics["total_visits"],
            "completed_count": metrics["completed_count"],
            "pending_count": metrics["pending_count"],
            "overdue_count": metrics["overdue_count"],
            "upcoming_count": metrics["upcoming_count"],
            "cadence": metrics["cadence"],
            "risks": ai_summary.get("risks", risks) if isinstance(ai_summary.get("risks"), list) else risks,
            "next_visit": {
                "due_date": next_visit["due"].isoformat() if next_visit and next_visit.get("due") else None,
                "text": next_visit.get("text") if next_visit else None,
            } if next_visit else None,
            "actions": ai_summary.get("actions", actions) if isinstance(ai_summary.get("actions"), list) else actions,
            "insights": ai_summary.get("insights", f"{patient.field_name} is under {patient.acres or 'Unknown'} care. {status_summary}."),
        }

        validated = PatientSummaryOutput.model_validate(result)
        trace_steps.append(AgentStepTrace(step="validate_output", status="ok", detail="Schema validation passed"))

        trace = AgentTrace(trace_id=trace_id, steps=trace_steps, fallback_used=fallback_used)
        payload = validated.model_dump()
        payload["_meta"] = {"trace_id": trace.trace_id, "fallback_used": trace.fallback_used}
        return payload

    except Exception as err:
        fallback_used = True
        trace_steps.append(AgentStepTrace(step="agent_fallback", status="fallback", detail=str(err)))

        patient = tool_get_patient(db, patient_id, uid)
        visits = tool_get_visits(db, patient_id)
        parsed_visits = tool_parse_visits(visits)
        metrics = tool_compute_metrics(patient, parsed_visits)
        risks = tool_classify_risks(patient, metrics)
        status_summary = tool_status_summary(patient, metrics)
        actions = tool_propose_actions(metrics)
        next_visit = metrics.get("next_visit")

        fallback_payload = {
            "patient_id": patient_id,
            "patient_name": patient.field_name,
            "status_summary": status_summary,
            "care_level": patient.acres or "Unknown",
            "description": patient.description or "",
            "adherence_30d": metrics["adherence_30d"],
            "total_visits": metrics["total_visits"],
            "completed_count": metrics["completed_count"],
            "pending_count": metrics["pending_count"],
            "overdue_count": metrics["overdue_count"],
            "upcoming_count": metrics["upcoming_count"],
            "cadence": metrics["cadence"],
            "risks": risks,
            "next_visit": {
                "due_date": next_visit["due"].isoformat() if next_visit and next_visit.get("due") else None,
                "text": next_visit.get("text") if next_visit else None,
            } if next_visit else None,
            "actions": actions,
            "insights": f"{patient.field_name} is under {patient.acres or 'Unknown'} care. {status_summary}.",
            "_meta": {"trace_id": trace_id, "fallback_used": True},
        }
        return fallback_payload

