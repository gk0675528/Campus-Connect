"""
Utility functions and helpers
"""

import json
from typing import Any, Dict
from decimal import Decimal


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def to_dict(obj) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary"""
    if hasattr(obj, '__table__'):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    return {}


def paginate(items: list, page: int = 1, page_size: int = 10):
    """Paginate items"""
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "page_size": page_size,
        "pages": (len(items) + page_size - 1) // page_size
    }
