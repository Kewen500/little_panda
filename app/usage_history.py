from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from app.config import CACHE_DIR
from app.models import BalanceSummary


PeriodName = Literal["hour", "day", "week", "month"]

MAX_HISTORY_POINTS = 2_000


@dataclass(slots=True)
class UsageSnapshot:
    provider_name: str
    balance: float | None
    currency: str | None
    recorded_at: datetime


@dataclass(slots=True)
class UsageBar:
    label: str
    value: float


def usage_history_path(provider_name: str) -> Path:
    safe_name = "".join(
        char for char in provider_name.lower() if char.isalnum() or char in ("-", "_")
    )
    return CACHE_DIR / f"{safe_name}_usage_history.json"


def record_usage_snapshot(summary: BalanceSummary) -> None:
    history = load_usage_history(summary.provider_name)
    recorded_at = summary.updated_at or datetime.now()
    history.append(
        UsageSnapshot(
            provider_name=summary.provider_name,
            balance=summary.balance,
            currency=summary.currency,
            recorded_at=recorded_at,
        )
    )
    save_usage_history(summary.provider_name, history[-MAX_HISTORY_POINTS:])


def load_usage_history(provider_name: str) -> list[UsageSnapshot]:
    path = usage_history_path(provider_name)
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(payload, list):
        return []

    snapshots: list[UsageSnapshot] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            recorded_at = datetime.fromisoformat(str(item.get("recorded_at")))
        except ValueError:
            continue
        snapshots.append(
            UsageSnapshot(
                provider_name=str(item.get("provider_name") or provider_name),
                balance=_to_float(item.get("balance")),
                currency=_to_str(item.get("currency")),
                recorded_at=recorded_at,
            )
        )
    return snapshots


def save_usage_history(provider_name: str, history: list[UsageSnapshot]) -> None:
    path = usage_history_path(provider_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "provider_name": snapshot.provider_name,
            "balance": snapshot.balance,
            "currency": snapshot.currency,
            "recorded_at": snapshot.recorded_at.isoformat(),
        }
        for snapshot in history
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def aggregate_usage(
    provider_name: str,
    period: PeriodName,
    now: datetime | None = None,
) -> list[UsageBar]:
    now = now or datetime.now()
    buckets = _make_buckets(period, now)
    values = [0.0 for _ in buckets]
    history = sorted(load_usage_history(provider_name), key=lambda item: item.recorded_at)

    for previous, current in zip(history, history[1:]):
        delta = _snapshot_delta(previous, current)
        if delta <= 0:
            continue
        bucket_index = _bucket_index(current.recorded_at, period, now)
        if bucket_index is not None and 0 <= bucket_index < len(values):
            values[bucket_index] += delta

    return [UsageBar(label=label, value=value) for label, value in zip(buckets, values)]


def _snapshot_delta(
    previous: UsageSnapshot,
    current: UsageSnapshot,
) -> float:
    if previous.balance is None or current.balance is None:
        return 0.0
    if previous.currency and current.currency and previous.currency != current.currency:
        return 0.0
    return max(previous.balance - current.balance, 0.0)


def _make_buckets(period: PeriodName, now: datetime) -> list[str]:
    if period == "hour":
        start = _floor_minute(now) - timedelta(minutes=55)
        return [(start + timedelta(minutes=5 * index)).strftime("%H:%M") for index in range(12)]
    if period == "day":
        return [f"{hour:02d}" for hour in range(24)]
    if period == "week":
        start = _start_of_day(now) - timedelta(days=6)
        return [(start + timedelta(days=index)).strftime("%m/%d") for index in range(7)]

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    return [f"{day}日" for day in range(1, days_in_month + 1)]


def _bucket_index(timestamp: datetime, period: PeriodName, now: datetime) -> int | None:
    if period == "hour":
        start = _floor_minute(now) - timedelta(minutes=55)
        if timestamp < start or timestamp > now:
            return None
        return int((timestamp - start).total_seconds() // 300)
    if period == "day":
        start = _start_of_day(now)
        if timestamp < start or timestamp >= start + timedelta(days=1):
            return None
        return timestamp.hour
    if period == "week":
        start = _start_of_day(now) - timedelta(days=6)
        if timestamp < start or timestamp >= start + timedelta(days=7):
            return None
        return (timestamp.date() - start.date()).days

    start = datetime(now.year, now.month, 1)
    next_month = (
        datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
    )
    if timestamp < start or timestamp >= next_month:
        return None
    return timestamp.day - 1


def _floor_minute(value: datetime) -> datetime:
    minute = value.minute - value.minute % 5
    return value.replace(minute=minute, second=0, microsecond=0)


def _start_of_day(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        multiplier = 1.0
        if cleaned[-1:].lower() == "k":
            cleaned = cleaned[:-1]
            multiplier = 1_000.0
        elif cleaned[-1:].lower() == "m":
            cleaned = cleaned[:-1]
            multiplier = 1_000_000.0
        elif cleaned[-1:].lower() == "b":
            cleaned = cleaned[:-1]
            multiplier = 1_000_000_000.0
        value = cleaned
    else:
        multiplier = 1.0
    try:
        return float(value) * multiplier
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> str | None:
    return str(value) if value not in (None, "") else None
