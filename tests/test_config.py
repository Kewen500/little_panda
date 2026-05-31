from __future__ import annotations

import unittest

from app.config import get_always_on_top


class ConfigTest(unittest.TestCase):
    def test_always_on_top_defaults_to_true(self) -> None:
        self.assertTrue(get_always_on_top({}))

    def test_always_on_top_can_be_disabled(self) -> None:
        self.assertFalse(get_always_on_top({"always_on_top": False}))


if __name__ == "__main__":
    unittest.main()
