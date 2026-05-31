from __future__ import annotations

import unittest

from app.balance_state import is_low_balance
from app.models import BalanceSummary


class BalanceStateTest(unittest.TestCase):
    def test_cny_below_five_is_low(self) -> None:
        summary = BalanceSummary("deepseek", balance=4.99, currency="CNY", is_available=True)

        self.assertTrue(is_low_balance(summary))

    def test_cny_five_is_not_low(self) -> None:
        summary = BalanceSummary("deepseek", balance=5.0, currency="CNY", is_available=True)

        self.assertFalse(is_low_balance(summary))

    def test_usd_is_converted_to_cny_estimate(self) -> None:
        low = BalanceSummary("deepseek", balance=0.5, currency="USD", is_available=True)
        enough = BalanceSummary("deepseek", balance=1.0, currency="USD", is_available=True)

        self.assertTrue(is_low_balance(low))
        self.assertFalse(is_low_balance(enough))

    def test_unavailable_is_treated_as_low(self) -> None:
        summary = BalanceSummary("kimi", balance=100, currency="CNY", is_available=False)

        self.assertTrue(is_low_balance(summary))


if __name__ == "__main__":
    unittest.main()

