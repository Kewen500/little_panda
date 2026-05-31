from __future__ import annotations

from app.models import BalanceSummary


LOW_BALANCE_CNY_THRESHOLD = 5.0
USD_TO_CNY_RATE = 7.2


def balance_as_cny(balance: float | None, currency: str | None) -> float | None:
    if balance is None:
        return None

    currency_code = (currency or "").upper()
    if currency_code == "USD":
        return balance * USD_TO_CNY_RATE
    return balance


def is_low_balance(summary: BalanceSummary) -> bool | None:
    if summary.is_available is False:
        return True

    cny_balance = balance_as_cny(summary.balance, summary.currency)
    if cny_balance is None:
        return None
    return cny_balance < LOW_BALANCE_CNY_THRESHOLD

