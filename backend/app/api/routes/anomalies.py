from fastapi import APIRouter, HTTPException
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.core.database import db
from app.ml.anomaly_detection import detect
from app.services.energy_service import format_timestamp, frame

router = APIRouter()


@router.get("/anomalies")
def anomalies(limit: int = 100):
    try:
        cursor = db.anomalies.find({}).sort("timestamp", -1).limit(max(1, min(limit, 1000)))
        items = []
        for doc in cursor:
            item_id = str(doc.pop("_id", ""))
            doc["id"] = item_id
            if "timestamp" in doc:
                doc["timestamp"] = format_timestamp(doc["timestamp"])
            items.append(doc)
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; anomaly records could not be loaded.") from exc
    if not items:
        raw_items = detect(frame())[-max(1, min(limit, 1000)):]
        items = []
        for i, doc in enumerate(raw_items):
            doc = dict(doc)
            doc["id"] = f"calc_{i}"
            if "timestamp" in doc:
                doc["timestamp"] = format_timestamp(doc["timestamp"])
            items.append(doc)
    return {"items": items, "count": len(items), "method": "robust rolling median absolute deviation"}


@router.get("/anomalies/{anomaly_id}")
def anomaly(anomaly_id: str):
    query = None
    try:
        query = {"_id": ObjectId(anomaly_id)}
    except Exception:
        query = {"id": anomaly_id}
    try:
        item = db.anomalies.find_one(query)
        if not item and query != {"id": anomaly_id}:
            item = db.anomalies.find_one({"id": anomaly_id})
    except PyMongoError as exc:
        raise HTTPException(503, "MongoDB is unavailable; anomaly detail could not be loaded.") from exc
    if not item:
        raise HTTPException(404, "Anomaly not found")
    item_id = str(item.pop("_id", anomaly_id))
    item["id"] = item_id
    if "timestamp" in item:
        item["timestamp"] = format_timestamp(item["timestamp"])
    return item
