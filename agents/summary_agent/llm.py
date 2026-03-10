"""
LLM narrative generation for patient summary agent.
"""
import json
from typing import Any, Dict, List

from config import OPENAI_API_KEY

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

client = None
if OPENAI_API_KEY and OpenAI is not None:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client = None


def generate_patient_summary(
    patient_data: Dict,
    visit_metrics: Dict,
    risks: List[Dict],
) -> Dict[str, Any]:
    if not client or not OPENAI_API_KEY:
        return _fallback_summary(patient_data, visit_metrics, risks)

    try:
        context = f"""
Patient: {patient_data['name']}
Care Level: {patient_data['care_level']}
Status: {'Active' if patient_data.get('active', True) else 'Discharged'}
Description: {patient_data.get('description', 'No description available')}

Visit Metrics:
- 30-day adherence: {visit_metrics.get('adherence_30d', 0):.1f}%
- Total visits: {visit_metrics.get('total_visits', 0)}
- Completed: {visit_metrics.get('completed_count', 0)}
- Pending: {visit_metrics.get('pending_count', 0)}
- Overdue: {visit_metrics.get('overdue_count', 0)}
- Upcoming: {visit_metrics.get('upcoming_count', 0)}
- Care cadence: {visit_metrics.get('cadence', 'Unknown')}

Risk Indicators:
{chr(10).join(f"- {risk.get('message', '')}" for risk in risks) if risks else "- None identified"}

Next Visit: {visit_metrics.get('next_visit_date', 'Not scheduled')}
"""

        prompt = f"""You are a care coordination AI assistant. Analyze this patient's care data and generate a concise, actionable summary.

{context}

Generate a JSON response with exactly these fields:
{{
  "status_summary": "One short phrase (e.g., 'On track', 'Needs attention', 'Behind schedule', 'Discharged')",
  "risks": [
    {{"level": "high|medium|info", "message": "Brief risk description"}}
  ],
  "actions": ["Action item 1", "Action item 2"],
  "insights": "2-3 sentence natural language summary of patient status and care needs"
}}

Be concise, clinical, and actionable. Focus on what care coordinators need to know immediately."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a healthcare care coordination assistant. Provide structured, actionable insights."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        ai_result = json.loads(content)
        return _coerce_summary_payload(ai_result, patient_data, visit_metrics, risks)

    except Exception:
        return _fallback_summary(patient_data, visit_metrics, risks)


def _fallback_summary(patient_data: Dict, visit_metrics: Dict, risks: List[Dict]) -> Dict[str, Any]:
    status_summary = visit_metrics.get("status_summary", "Active care")
    if not patient_data.get("active", True):
        status_summary = "Discharged"
    return {
        "status_summary": status_summary,
        "risks": risks,
        "actions": visit_metrics.get("actions", []),
        "insights": f"{patient_data['name']} is under {patient_data['care_level']} care. {status_summary}.",
    }


def _coerce_summary_payload(ai_result: Dict, patient_data: Dict, visit_metrics: Dict, risks: List[Dict]) -> Dict[str, Any]:
    status_summary = ai_result.get("status_summary") or visit_metrics.get("status_summary", "Active care")
    insights = ai_result.get("insights") or f"{patient_data['name']} is under {patient_data['care_level']} care. {status_summary}."

    ai_risks = ai_result.get("risks")
    safe_risks = ai_risks if isinstance(ai_risks, list) else risks

    ai_actions = ai_result.get("actions")
    safe_actions = ai_actions if isinstance(ai_actions, list) and ai_actions else visit_metrics.get("actions", [])

    return {
        "status_summary": str(status_summary),
        "risks": safe_risks,
        "actions": safe_actions,
        "insights": str(insights),
    }

