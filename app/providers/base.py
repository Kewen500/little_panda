from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import BalanceSummary


class ProviderError(RuntimeError):
    """Raised when a provider cannot return usage data."""


class BalanceProvider(ABC):
    provider_name = "base"

    @abstractmethod
    def fetch_balance(self) -> BalanceSummary:
        """Fetch current balance data from the provider."""
