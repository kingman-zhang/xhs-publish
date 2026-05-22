from functools import lru_cache

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .config import get_settings


@lru_cache
def get_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongo_url)


def get_database() -> Database:
    settings = get_settings()
    return get_client()[settings.mongo_db_name]


def get_notes_collection() -> Collection:
    return get_database()["notes"]


def get_assets_collection() -> Collection:
    return get_database()["assets"]
