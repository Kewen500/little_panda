from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import CACHE_DIR
from app.models import BalanceSummary


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def balance_cache_path(provider_name: str) -> Path:
    safe_name = "".join(
        char for char in provider_name.lower() if char.isalnum() or char in ("-", "_")
    )
    return CACHE_DIR / f"{safe_name}_balance.json"


def save_balance_cache(summary: BalanceSummary) -> None:
    path = balance_cache_path(summary.provider_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider_name": summary.provider_name,
        "balance": summary.balance,
        "currency": summary.currency,
        "is_available": summary.is_available,
        "updated_at": _serialize_datetime(summary.updated_at),
        "raw_detail": summary.raw_detail,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_balance_cache(provider_name: str) -> BalanceSummary | None:
    path = balance_cache_path(provider_name)
    if not path.exists():
        return None

    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        updated_at = payload.get("updated_at")
        return BalanceSummary(
            provider_name=str(payload.get("provider_name") or provider_name),
            balance=payload.get("balance"),
            currency=payload.get("currency"),
            is_available=payload.get("is_available"),
            updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
            raw_detail=payload.get("raw_detail"),
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
