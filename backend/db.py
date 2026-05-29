"""MongoDB async client for the Murmur orchestrator."""
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings

client = AsyncIOMotorClient(settings.mongo_url)
db = client[settings.db_name]

# Collections
turns_collection = db["turns"]
bench_runs_collection = db["bench_runs"]
