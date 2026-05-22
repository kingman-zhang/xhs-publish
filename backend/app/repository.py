from datetime import datetime
from typing import Any

from pymongo import ASCENDING, DESCENDING

from .database import get_assets_collection, get_notes_collection


def init_indexes() -> None:
    notes = get_notes_collection()
    assets = get_assets_collection()
    notes.create_index([("deletedAt", ASCENDING), ("updatedAt", DESCENDING)])
    notes.create_index([("title", ASCENDING)])
    notes.create_index([("body", ASCENDING)])
    notes.create_index("shareToken", unique=True)
    assets.create_index("noteId")


def create_note(document: dict[str, Any]) -> None:
    get_notes_collection().insert_one(document)


def update_note(note_id: str, update: dict[str, Any]) -> None:
    get_notes_collection().update_one({"id": note_id}, {"$set": update})


def get_note(note_id: str) -> dict[str, Any] | None:
    return get_notes_collection().find_one({"id": note_id, "deletedAt": None}, {"_id": 0})


def get_note_by_share_token(token: str) -> dict[str, Any] | None:
    return get_notes_collection().find_one({"shareToken": token, "deletedAt": None}, {"_id": 0})


def list_notes(keyword: str | None, skip: int, limit: int) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"deletedAt": None}
    if keyword:
        query["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"body": {"$regex": keyword, "$options": "i"}},
        ]
    cursor = (
        get_notes_collection()
        .find(query, {"_id": 0})
        .sort("updatedAt", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)


def soft_delete_note(note_id: str, deleted_at: datetime) -> None:
    get_notes_collection().update_one({"id": note_id}, {"$set": {"deletedAt": deleted_at, "updatedAt": deleted_at}})


def create_asset(document: dict[str, Any]) -> None:
    get_assets_collection().insert_one(document)


def get_assets_by_ids(asset_ids: list[str]) -> list[dict[str, Any]]:
    if not asset_ids:
        return []
    items = list(get_assets_collection().find({"id": {"$in": asset_ids}}, {"_id": 0}))
    ordering = {asset_id: index for index, asset_id in enumerate(asset_ids)}
    items.sort(key=lambda item: ordering.get(item["id"], 0))
    return items


def get_asset(asset_id: str) -> dict[str, Any] | None:
    return get_assets_collection().find_one({"id": asset_id}, {"_id": 0})


def delete_asset(asset_id: str) -> None:
    get_assets_collection().delete_one({"id": asset_id})


def bind_assets_to_note(asset_ids: list[str], note_id: str) -> None:
    if asset_ids:
        get_assets_collection().update_many({"id": {"$in": asset_ids}}, {"$set": {"noteId": note_id}})
