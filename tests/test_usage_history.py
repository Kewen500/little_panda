from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from app import usage_history
from app.models import BalanceSummary
from app.usage_history import (
    UsageSnapshot,
    aggregate_usage,
    extract_token_total,
    load_usage_history,
    record_usage_snapshot,
    save_usage_history,
)


class UsageHistoryTest(unittest.TestCase):
    def test_extracts_nested_token_total(self) -> None:
        payload = {"data": {"usage": {"total_tokens": "143.4M"}}}

        self.assertEqual(extract_token_total(payload), 143_400_000)

    def test_aggregates_weekly_cost_from_balance_drop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            provider = "example"
            now = datetime(2026, 6, 1, 12, 0, 0)
            with patch.object(usage_history, "CACHE_DIR", Path(temp_dir)):
                save_usage_history(
                    provider,
                    [
                        UsageSnapshot(provider, 30.0, "CNY", None, now - timedelta(days=1)),
                        UsageSnapshot(provider, 25.5, "CNY", None, now),
                    ],
                )

                bars = aggregate_usage(provider, "cost", "week", now)

        self.assertEqual(bars[-1].value, 4.5)

    def test_records_snapshot_to_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            provider = "example"
            with patch.object(usage_history, "CACHE_DIR", Path(temp_dir)):
                record_usage_snapshot(
                    BalanceSummary(
                        provider,
                        balance=12.5,
                        currency="CNY",
                        raw_detail={"data": {"total_tokens": 100}},
                        updated_at=datetime(2026, 6, 1, 12, 0, 0),
                    )
                )

                history = load_usage_history(provider)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].balance, 12.5)
        self.assertEqual(history[0].token_total, 100)


if __name__ == "__main__":
    unittest.main()
