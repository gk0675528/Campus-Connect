"""Generic document operations for unstructured application data."""

from typing import Any, Mapping, Optional

from bson import ObjectId

from core.config.mongodb import get_mongodb


async def insert_document(collection: str, document: Mapping[str, Any]) -> str:
    """Insert a document and return its MongoDB identifier as a string."""
    database = await get_mongodb()
    if database is None:
        raise RuntimeError("MongoDB document store is unavailable")

    result = await database[collection].insert_one(dict(document))
    return str(result.inserted_id)


async def get_document(collection: str, document_id: str) -> Optional[dict[str, Any]]:
    """Fetch one document by its MongoDB identifier."""
    database = await get_mongodb()
    if database is None:
        raise RuntimeError("MongoDB document store is unavailable")

    document = await database[collection].find_one({"_id": ObjectId(document_id)})
    if document is not None:
        document["_id"] = str(document["_id"])
    return document


async def update_document(
    collection: str,
    document_id: str,
    updates: Mapping[str, Any],
) -> bool:
    """Update one document and report whether it existed."""
    database = await get_mongodb()
    if database is None:
        raise RuntimeError("MongoDB document store is unavailable")

    result = await database[collection].update_one(
        {"_id": ObjectId(document_id)},
        {"$set": dict(updates)},
    )
    return result.matched_count == 1


async def delete_document(collection: str, document_id: str) -> bool:
    """Delete one document and report whether it existed."""
    database = await get_mongodb()
    if database is None:
        raise RuntimeError("MongoDB document store is unavailable")

    result = await database[collection].delete_one({"_id": ObjectId(document_id)})
    return result.deleted_count == 1