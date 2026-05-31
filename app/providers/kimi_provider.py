from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models import BalanceSummary
from app.providers.base import BalanceProvider, ProviderError


class KimiProvider(BalanceProvider):
    provider_name = "kimi"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.api_key = str(self.config.get("api_key", "")).strip()
        self.base_url = str(
            self.config.get("base_url") or "https://api.moonshot.cn"
        ).strip()
        self.balance_endpoint = str(
            self.config.get("balance_endpoint") or "/v1/users/me/balance"
        ).strip()

    def fetch_balance(self) -> BalanceSummary:
        self.validate_configuration()

        try:
            import requests
        except ImportError as exc:
            raise ProviderError("KimiProvider \u9700\u8981\u5b89\u88c5 requests\u3002") from exc

        try:
            response = requests.get(
                self._balance_url(),
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15,
            )
            if response.status_code in (401, 403):
                raise ProviderError("Kimi API key \u88ab\u5b98\u65b9\u63a5\u53e3\u62d2\u7edd\u3002")
            response.raise_for_status()
            payload = response.json()
        except ProviderError:
            raise
        except requests.RequestException as exc:
            raise ProviderError(f"Kimi \u4f59\u989d\u8bf7\u6c42\u5931\u8d25\uff1a{exc}") from exc
        except ValueError as exc:
            raise ProviderError("Kimi \u4f59\u989d\u54cd\u5e94\u4e0d\u662f\u6709\u6548 JSON\u3002") from exc

        return self.parse_balance_response(payload)

    def validate_configuration(self) -> None:
        if not self.api_key:
            raise ProviderError("\u8bf7\u5728\u8d26\u6237\u7a97\u53e3\u586b\u5199 Kimi API Key\u3002")
        if not self.base_url:
            raise ProviderError("\u8bf7\u5728\u8d26\u6237\u7a97\u53e3\u586b\u5199 Kimi URL\u3002")
        if not self.balance_endpoint:
            raise ProviderError("\u8bf7\u5728\u8d26\u6237\u7a97\u53e3\u586b\u5199 Kimi \u4f59\u989d\u63a5\u53e3\u3002")

    def parse_balance_response(self, payload: dict[str, Any]) -> BalanceSummary:
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

        return BalanceSummary(
            provider_name=self.provider_name,
            balance=self._to_float(data.get("available_balance")),
            currency="CNY",
            is_available=self._to_bool(payload.get("status")),
            updated_at=datetime.now(),
            raw_detail=payload,
        )

    def _balance_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.balance_endpoint.lstrip('/')}"

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_bool(value: Any) -> bool | None:
        if value is None:
            return None
        return bool(value)
