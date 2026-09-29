from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import run
from app.core.database import db
from app.models.query import AgentRunRequest
from pymongo.errors import PyMongoError

router = APIRouter()


@router.post("/agents/run")
def run_agents(body: AgentRunRequest):
    question = body.question or body.query or "Manual agent run"
    from app.api.routes.query import classify
    if body.task and body.task in {"anomaly_detection", "insights", "evening_increase", "peak_demand", "hourly_analysis", "weekday_weekend_comparison", "trends", "forecast"}:
        intent = body.task
    elif body.query or body.question:
        intent, _ = classify(question)
    else:
        intent = "insights"
    trace_id, messages, trace = run(question, intent, body.hours)
    return {"trace_id": trace_id, "agents": trace}


@router.get("/agents/trace/{trace_id}")
def get_trace(trace_id: str):
    try:
        doc = db.agent_traces.find_one({"trace_id": trace_id}, {"_id": 0})
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; agent trace could not be loaded.") from exc
    if not doc:
        raise HTTPException(404, "Trace not found")
    return doc
