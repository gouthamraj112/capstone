def run(message):
    facts = message["data"].get("findings", [])
    evidence = message.get("evidence", [])
    values = {item.get("label"): item.get("value") for item in evidence if item.get("label")}
    overall = values.get("Overall mean demand")
    evening = values.get("Mean demand (18:00-21:00)") or values.get("Mean demand (18:00–21:00)")
    recommendations = []
    if overall and evening is not None and evening > overall:
        recommendations.append({"text": "Monitor the 18:00-21:00 period when evaluating demand-response or load-management strategies.",
                                "evidence": ["Evening mean demand", "Overall mean demand"]})
    return {"source_agent": "decision_support_agent", "target_agent": "response", "task": "recommendation",
            "data": {"finding_count": len(facts), "recommendations": recommendations}, "evidence": evidence,
            "confidence": message.get("confidence", 0)}
