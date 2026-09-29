from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings

client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1200)
db = client[settings.database_name]
COLLECTIONS = ("energy_data", "hourly_energy", "daily_energy", "anomalies", "forecasts", "agent_traces", "query_history")


def ensure_indexes():
    existing = set(db.list_collection_names())
    for name in COLLECTIONS:
        if name not in existing:
            db.create_collection(name)
    db.energy_data.create_index([("timestamp", ASCENDING)], unique=True)
    db.energy_data.create_index([("Global_active_power", DESCENDING)])
    for name, field in (("hourly_energy", "timestamp"), ("daily_energy", "date"), ("anomalies", "timestamp"), ("forecasts", "timestamp")):
        db[name].create_index([(field, DESCENDING)])
    db.energy_data.create_index([("year", ASCENDING), ("month", ASCENDING), ("hour", ASCENDING)])
    db.agent_traces.create_index([("trace_id", ASCENDING)], unique=True, sparse=True)
    db.query_history.create_index([("created_at", DESCENDING)])


def database_status() -> tuple[bool, str]:
    try:
        client.admin.command("ping")
        return True, "connected"
    except PyMongoError:
        return False, "MongoDB is unavailable"
