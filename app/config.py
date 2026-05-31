from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


APP_NAME = "API \u4f59\u989d\u6302\u4ef6"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / ".cache"
PROVIDERS_CONFIG_FILE = PROJECT_ROOT / "config" / "providers.json"

DEFAULT_PROVIDER_CONFIG: dict[str, Any] = {
    "active_provider": "deepseek",
    "refresh_interval_seconds": 300,
    "always_on_top": True,
    "providers": {
        "deepseek": {
            "enabled": True,
            "balance_endpoint": "/user/balance",
        },
        "kimi": {
            "enabled": True,
            "balance_endpoint": "/v1/users/me/balance",
        },
    },
}


def load_provider_config() -> dict[str, Any]:
    if not PROVIDERS_CONFIG_FILE.exists():
        return deepcopy(DEFAULT_PROVIDER_CONFIG)

    try:
        loaded = json.loads(PROVIDERS_CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return deepcopy(DEFAULT_PROVIDER_CONFIG)

    config = deepcopy(DEFAULT_PROVIDER_CONFIG)
    config.update({key: value for key, value in loaded.items() if key != "providers"})
    for name, provider_settings in loaded.get("providers", {}).items():
        if isinstance(provider_settings, dict) and isinstance(
            config["providers"].get(name), dict
        ):
            config["providers"][name].update(provider_settings)
        else:
            config["providers"][name] = provider_settings
    return config


def get_refresh_interval_seconds(config: dict[str, Any]) -> int:
    value = config.get("refresh_interval_seconds")
    if isinstance(value, int) and value > 0:
        return value
    return DEFAULT_PROVIDER_CONFIG["refresh_interval_seconds"]


def get_always_on_top(config: dict[str, Any]) -> bool:
    value = config.get("always_on_top")
    return value if isinstance(value, bool) else DEFAULT_PROVIDER_CONFIG["always_on_top"]


def save_provider_config(config: dict[str, Any]) -> None:
    PROVIDERS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROVIDERS_CONFIG_FILE.write_text(
        json.dumps(config, indent=2),
        encoding="utf-8",
    )
