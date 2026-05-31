from __future__ import annotations

from typing import Any

from app.accounts import account_for_provider
from app.providers.base import BalanceProvider, ProviderError
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.custom_balance_provider import CustomBalanceProvider
from app.providers.kimi_provider import KimiProvider


def build_provider(config: dict[str, Any]) -> BalanceProvider:
    active_provider = config.get("active_provider", "deepseek")
    providers = config.get("providers", {})
    account = account_for_provider(active_provider)
    provider_config = dict(providers.get(active_provider, {}))
    provider_config.update(account)

    if active_provider == "deepseek":
        return DeepSeekProvider(provider_config)
    if active_provider == "kimi":
        return KimiProvider(provider_config)
    if account:
        return CustomBalanceProvider(active_provider, provider_config)
    raise ProviderError(f"\u4e0d\u652f\u6301\u7684\u5e73\u53f0\uff1a{active_provider}")
