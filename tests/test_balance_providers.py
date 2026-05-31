from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.providers.base import ProviderError
from app.providers.custom_balance_provider import CustomBalanceProvider
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.kimi_provider import KimiProvider


FIXTURES = Path(__file__).parent / "fixtures"


class BalanceProviderTest(unittest.TestCase):
    def test_deepseek_parses_total_balance_and_currency(self) -> None:
        payload = json.loads((FIXTURES / "deepseek_balance_response.json").read_text())

        summary = DeepSeekProvider().parse_balance_response(payload)

        self.assertEqual(summary.provider_name, "deepseek")
        self.assertEqual(summary.balance, 110.0)
        self.assertEqual(summary.currency, "CNY")
        self.assertTrue(summary.is_available)

    def test_deepseek_prefers_cny_when_multiple_currencies_have_balance(self) -> None:
        payload = {
            "is_available": True,
            "balance_infos": [
                {"currency": "CNY", "total_balance": "110.00"},
                {"currency": "USD", "total_balance": "4.94"},
            ],
        }

        summary = DeepSeekProvider().parse_balance_response(payload)

        self.assertEqual(summary.balance, 110.0)
        self.assertEqual(summary.currency, "CNY")

    def test_deepseek_uses_cny_when_usd_is_zero_and_cny_has_balance(self) -> None:
        payload = {
            "is_available": True,
            "balance_infos": [
                {"currency": "USD", "total_balance": "0.00"},
                {"currency": "CNY", "total_balance": "10.00"},
            ],
        }

        summary = DeepSeekProvider().parse_balance_response(payload)

        self.assertEqual(summary.balance, 10.0)
        self.assertEqual(summary.currency, "CNY")

    def test_deepseek_uses_usd_when_cny_is_zero_and_usd_has_balance(self) -> None:
        payload = {
            "is_available": True,
            "balance_infos": [
                {"currency": "CNY", "total_balance": "0.00"},
                {"currency": "USD", "total_balance": "5.00"},
            ],
        }

        summary = DeepSeekProvider().parse_balance_response(payload)

        self.assertEqual(summary.balance, 5.0)
        self.assertEqual(summary.currency, "USD")

    def test_deepseek_uses_cny_when_all_currencies_are_zero(self) -> None:
        payload = {
            "is_available": True,
            "balance_infos": [
                {"currency": "USD", "total_balance": "0.00"},
                {"currency": "CNY", "total_balance": "0.00"},
            ],
        }

        summary = DeepSeekProvider().parse_balance_response(payload)

        self.assertEqual(summary.balance, 0.0)
        self.assertEqual(summary.currency, "CNY")

    def test_kimi_parses_available_balance(self) -> None:
        payload = json.loads((FIXTURES / "kimi_balance_response.json").read_text())

        summary = KimiProvider().parse_balance_response(payload)

        self.assertEqual(summary.provider_name, "kimi")
        self.assertEqual(summary.balance, 49.58894)
        self.assertEqual(summary.currency, "CNY")
        self.assertTrue(summary.is_available)

    def test_missing_api_key_has_clear_error(self) -> None:
        provider = DeepSeekProvider()

        with self.assertRaisesRegex(ProviderError, "账户窗口"):
            provider.validate_configuration()

    def test_missing_balance_fields_do_not_crash(self) -> None:
        deepseek_summary = DeepSeekProvider().parse_balance_response(
            {"is_available": False, "balance_infos": [{}]}
        )
        kimi_summary = KimiProvider().parse_balance_response({"status": False, "data": {}})

        self.assertIsNone(deepseek_summary.balance)
        self.assertIsNone(deepseek_summary.currency)
        self.assertFalse(deepseek_summary.is_available)
        self.assertIsNone(kimi_summary.balance)
        self.assertEqual(kimi_summary.currency, "CNY")
        self.assertFalse(kimi_summary.is_available)

    def test_custom_provider_maps_balance_fields(self) -> None:
        provider = CustomBalanceProvider(
            "custom-example",
            {
                "balance_path": "result.account.balance",
                "currency_path": "result.account.currency",
                "available_path": "result.enabled",
            },
        )

        summary = provider.parse_balance_response(
            {
                "result": {
                    "account": {"balance": "12.50", "currency": "USD"},
                    "enabled": True,
                }
            }
        )

        self.assertEqual(summary.provider_name, "custom-example")
        self.assertEqual(summary.balance, 12.5)
        self.assertEqual(summary.currency, "USD")
        self.assertTrue(summary.is_available)

    def test_custom_provider_parses_false_string_status(self) -> None:
        provider = CustomBalanceProvider(
            "custom-example",
            {
                "balance_path": "balance",
                "available_path": "available",
            },
        )

        summary = provider.parse_balance_response(
            {"balance": "3.00", "available": "false"}
        )

        self.assertFalse(summary.is_available)

    def test_custom_provider_uses_authorization_header(self) -> None:
        provider = CustomBalanceProvider(
            "token-example",
            {
                "api_key": "secret-token",
                "base_url": "https://example.com",
                "balance_endpoint": "/api/v1/me",
                "balance_path": "data.user.balance",
            },
        )

        self.assertEqual(provider._auth_headers(), {"Authorization": "Bearer secret-token"})

    def test_custom_provider_requires_api_key(self) -> None:
        provider = CustomBalanceProvider(
            "token-example",
            {
                "base_url": "https://example.com",
                "balance_endpoint": "/api/v1/me",
                "balance_path": "data.user.balance",
            },
        )

        with self.assertRaisesRegex(ProviderError, "API Key"):
            provider.validate_configuration()


if __name__ == "__main__":
    unittest.main()
