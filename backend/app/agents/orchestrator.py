import logging
from time import perf_counter

from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError

from app.agents import anomaly_agent, decision_support_agent, energy_data_agent, energy_insight_agent, forecasting_agent
from app.core.database import db

logger = logging.getLogger(__name__)


def run(question: str, intent: str, hours: int = 6, start_date=None, end_date=None):
    messages, trace = [], []

    def execute(agent, *args):
        function = agent.run if hasattr(agent, "run") else agent
        name = function.__module__.rsplit(".", 1)[-1]
        started = perf_counter()
        status = "completed"
        try:
            message = function(*args)
        except HTTPException:
            raise
        except Exception:
            logger.exception("Agent %s failed", name)
            status = "failed"
            message = {"source_agent": name, "target_agent": "orchestrator", "task": "agent_failure",
                       "data": {"error": "Analysis failed; check backend logs and retry."}, "evidence": [], "confidence": 0.0}
        message.setdefault("source_agent", name)
        message["execution_ms"] = round((perf_counter() - started) * 1000, 2)
        message["status"] = status
        messages.append(message)
        trace.append(dict(message))
        return message

    needs_energy = intent in {"peak_demand", "hourly_analysis", "weekday_weekend_comparison", "trends", "insights", "evening_increase"}
    needs_anomaly = intent in {"anomaly_detection", "insights", "evening_increase"}
    needs_forecast = intent in {"forecast", "insights"}
    if needs_energy:
        execute(energy_data_agent.run, None, start_date, end_date)
    if needs_anomaly:
        execute(anomaly_agent.run, None, start_date, end_date)
    if needs_forecast:
        execute(forecasting_agent.run, None, hours)
    insight = execute(energy_insight_agent.run, messages)
    execute(decision_support_agent.run, insight)

    trace_id = str(ObjectId())
    try:
        db.agent_traces.insert_one({"_id": ObjectId(trace_id), "trace_id": trace_id, "question": question, "intent": intent,
                                    "agents": trace})
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; agent trace could not be saved.") from exc
    return trace_id, messages, trace
