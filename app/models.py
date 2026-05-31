from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


Number = Optional[float]
@dataclass(slots=True)
class BalanceSummary:
    provider_name: str
    balance: Number = None
    currency: Optional[str] = None
    is_available: Optional[bool] = None
    updated_at: Optional[datetime] = None
    raw_detail: Optional[dict] = None
