from __future__ import annotations

import base64
import ctypes
import json
from copy import deepcopy
from ctypes import wintypes
from pathlib import Path
from uuid import uuid4

from app.config import CACHE_DIR


ACCOUNTS_FILE = CACHE_DIR / "accounts.json"

DEFAULT_ACCOUNTS: dict[str, dict[str, str]] = {
    "deepseek": {
        "name": "DeepSeek",
        "provider_type": "deepseek",
        "base_url": "https://api.deepseek.com",
        "balance_endpoint": "/user/balance",
        "balance_path": "",
        "currency_path": "",
        "available_path": "",
        "currency_default": "",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_key": "",
    },
    "kimi": {
        "name": "Kimi",
        "provider_type": "kimi",
        "base_url": "https://api.moonshot.cn",
        "balance_endpoint": "/v1/users/me/balance",
        "balance_path": "",
        "currency_path": "",
        "available_path": "",
        "currency_default": "CNY",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_key": "",
    },
}


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _protect_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    data = api_key.encode("utf-8")
    buffer = ctypes.create_string_buffer(data)
    input_blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    output_blob = _DataBlob()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(input_blob), None, None, None, None, 0x01, ctypes.byref(output_blob)
    ):
        raise ctypes.WinError()
    try:
        encrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        return base64.b64encode(encrypted).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def _unprotect_api_key(encrypted_api_key: str) -> str:
    if not encrypted_api_key:
        return ""
    data = base64.b64decode(encrypted_api_key)
    buffer = ctypes.create_string_buffer(data)
    input_blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    output_blob = _DataBlob()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(input_blob), None, None, None, None, 0x01, ctypes.byref(output_blob)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def new_custom_account(name: str = "自定义平台") -> tuple[str, dict[str, str]]:
    account_id = f"custom-{uuid4().hex[:8]}"
    return account_id, {
        "name": name,
        "provider_type": "custom",
        "base_url": "",
        "balance_endpoint": "",
        "balance_path": "data.balance",
        "currency_path": "data.currency",
        "available_path": "data.is_available",
        "currency_default": "CNY",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer",
        "api_key": "",
    }


def load_accounts(path: Path = ACCOUNTS_FILE) -> dict[str, dict[str, str]]:
    accounts = deepcopy(DEFAULT_ACCOUNTS)
    if not path.exists():
        return accounts

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return accounts

    if not isinstance(loaded, dict):
        return accounts
    for account_id, stored_account in loaded.items():
        if not isinstance(stored_account, dict):
            continue
        account = accounts.setdefault(str(account_id), {})
        for key, value in stored_account.items():
            if key not in {"api_key_encrypted", "cookie_encrypted", "cookie", "auth_mode"}:
                account[str(key)] = str(value)
        try:
            account["api_key"] = _unprotect_api_key(
                str(stored_account.get("api_key_encrypted", ""))
            )
        except (OSError, ValueError):
            account["api_key"] = ""
    for account_id, default_account in DEFAULT_ACCOUNTS.items():
        account = accounts[account_id]
        for key in ("name", "provider_type", "base_url", "balance_endpoint"):
            if not account.get(key):
                account[key] = default_account[key]
    return accounts


def save_accounts(
    accounts: dict[str, dict[str, str]],
    path: Path = ACCOUNTS_FILE,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        account_id: {
            **{
                key: value
                for key, value in account.items()
                if key not in {"api_key", "cookie", "cookie_encrypted", "auth_mode"}
            },
            "api_key_encrypted": _protect_api_key(account.get("api_key", "")),
        }
        for account_id, account in accounts.items()
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def account_for_provider(
    account_id: str,
    path: Path = ACCOUNTS_FILE,
) -> dict[str, str]:
    return load_accounts(path).get(account_id, {})


def account_display_name(account_id: str, account: dict[str, str]) -> str:
    return account.get("name") or account_id
