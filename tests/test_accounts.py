from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.accounts import (
    account_for_provider,
    load_accounts,
    new_custom_account,
    save_accounts,
)


class AccountsTest(unittest.TestCase):
    def test_defaults_include_official_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            accounts = load_accounts(Path(temp_dir) / "missing.json")

        self.assertEqual(accounts["deepseek"]["base_url"], "https://api.deepseek.com")
        self.assertEqual(accounts["kimi"]["base_url"], "https://api.moonshot.cn")
        self.assertEqual(accounts["deepseek"]["api_key"], "")

    def test_saves_api_key_to_local_accounts_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "accounts.json"
            accounts = load_accounts(path)
            accounts["kimi"]["api_key"] = "test-kimi-key"
            save_accounts(accounts, path)

            kimi = account_for_provider("kimi", path)
            saved_text = path.read_text(encoding="utf-8")

        self.assertEqual(kimi["api_key"], "test-kimi-key")
        self.assertNotIn("test-kimi-key", saved_text)

    def test_saving_one_provider_keeps_the_other_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "accounts.json"
            accounts = load_accounts(path)
            accounts["deepseek"]["api_key"] = "deepseek-key"
            accounts["kimi"]["api_key"] = "kimi-key"
            save_accounts(accounts, path)

            loaded = load_accounts(path)

        self.assertEqual(loaded["deepseek"]["api_key"], "deepseek-key")
        self.assertEqual(loaded["kimi"]["api_key"], "kimi-key")

    def test_saves_custom_account(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "accounts.json"
            accounts = load_accounts(path)
            account_id, account = new_custom_account("Example")
            account["base_url"] = "https://api.example.com"
            account["balance_endpoint"] = "/balance"
            account["api_key"] = "example-key"
            accounts[account_id] = account
            save_accounts(accounts, path)

            loaded = account_for_provider(account_id, path)

        self.assertEqual(loaded["name"], "Example")
        self.assertEqual(loaded["base_url"], "https://api.example.com")
        self.assertEqual(loaded["api_key"], "example-key")

    def test_migrates_missing_builtin_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "accounts.json"
            path.write_text(
                '{"deepseek":{"base_url":"https://api.deepseek.com",'
                '"balance_endpoint":"","api_key_encrypted":""}}',
                encoding="utf-8",
            )

            loaded = load_accounts(path)

        self.assertEqual(loaded["deepseek"]["balance_endpoint"], "/user/balance")

    def test_drops_legacy_cookie_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "accounts.json"
            path.write_text(
                '{"custom-old":{"name":"Old","provider_type":"custom",'
                '"auth_mode":"cookie","cookie":"session=secret-cookie",'
                '"cookie_encrypted":"ignored","api_key_encrypted":""}}',
                encoding="utf-8",
            )

            loaded = account_for_provider("custom-old", path)
            save_accounts(load_accounts(path), path)
            saved_text = path.read_text(encoding="utf-8")

        self.assertNotIn("cookie", loaded)
        self.assertNotIn("auth_mode", loaded)
        self.assertNotIn("session=secret-cookie", saved_text)
        self.assertNotIn("cookie_encrypted", saved_text)


if __name__ == "__main__":
    unittest.main()
