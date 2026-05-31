from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models import BalanceSummary
from app.providers.base import BalanceProvider, ProviderError


class CustomBalanceProvider(BalanceProvider):
    def __init__(self, account_id: str, config: dict[str, Any]) -> None:
        self.provider_name = account_id
        self.config = config
        self.api_key = str(config.get("api_key", "")).strip()
        self.base_url = str(config.get("base_url", "")).strip()
        self.balance_endpoint = str(config.get("balance_endpoint", "")).strip()
        self.balance_path = str(config.get("balance_path", "data.balance")).strip()
        self.currency_path = str(config.get("currency_path", "")).strip()
        self.available_path = str(config.get("available_path", "")).strip()
        self.currency_default = str(config.get("currency_default", "CNY")).strip()
        self.auth_header = str(config.get("auth_header", "Authorization")).strip()
        self.auth_prefix = str(config.get("auth_prefix", "Bearer")).strip()

    def fetch_balance(self) -> BalanceSummary:
        self.validate_configuration()
        try:
            import requests
        except ImportError as exc:
            raise ProviderError("CustomBalanceProvider 需要安装 requests。") from exc

        try:
            response = requests.get(
                self._balance_url(),
                headers=self._auth_headers(),
                timeout=15,
            )
            if response.status_code in (401, 403):
                raise ProviderError("登录凭据被平台接口拒绝，请重新填写 API Key。")
            response.raise_for_status()
            payload = response.json()
        except ProviderError:
            raise
        except requests.RequestException as exc:
            raise ProviderError(f"余额请求失败：{exc}") from exc
        except ValueError as exc:
            raise ProviderError("余额响应不是有效 JSON。") from exc
        return self.parse_balance_response(payload)

    def validate_configuration(self) -> None:
        if not self.api_key:
            raise ProviderError("请在账户窗口填写 API Key。")
        if not self.base_url:
            raise ProviderError("请在账户窗口填写 URL。")
        if not self.balance_endpoint:
            raise ProviderError("请在账户窗口填写余额接口。")
        if not self.balance_path:
            raise ProviderError("请在账户窗口填写余额字段路径。")
        if not self.auth_header:
            raise ProviderError("请在账户窗口填写鉴权请求头。")

    def parse_balance_response(self, payload: dict[str, Any]) -> BalanceSummary:
        available = self._get_path(payload, self.available_path)
        return BalanceSummary(
            provider_name=self.provider_name,
            balance=self._to_float(self._get_path(payload, self.balance_path)),
            currency=self._to_str(self._get_path(payload, self.currency_path))
            or self.currency_default
            or None,
            is_available=self._to_bool(available),
            updated_at=datetime.now(),
            raw_detail=payload,
        )

    def _balance_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.balance_endpoint.lstrip('/')}"

    def _auth_headers(self) -> dict[str, str]:
        return {self.auth_header: f"{self.auth_prefix} {self.api_key}".strip()}

    @staticmethod
    def _get_path(payload: Any, path: str) -> Any:
        if not path:
            return None
        current = payload
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
                current = current[int(part)]
            else:
                return None
        return current

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_str(value: Any) -> str | None:
        return str(value) if value not in (None, "") else None

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip().lower() not in {"", "0", "false", "no", "off"}
        return bool(value)
