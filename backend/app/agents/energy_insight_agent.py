def run(messages):
    return {"source_agent": "energy_insight_agent", "target_agent": "decision_support_agent", "task": "synthesize",
            "data": {"findings": [m["task"] for m in messages]},
            "evidence": [e for m in messages for e in m.get("evidence", [])],
            "citations": [c for m in messages for c in m.get("citations", [])],
            "confidence": min((m.get("confidence", 0) for m in messages), default=0)}
