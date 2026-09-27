"""Faz 17 G.1-motor (RG-06): per-symbol margin-mode ownership lock -- two
independent owners (bots/deals) must not fight over the same symbol's
venue-global marginType."""
import unittest

from dcabot.application.margin_mode_registry import (
    MarginModeRegistryError,
    MarginModeSymbolRegistry,
)


class AcquireReleaseTests(unittest.TestCase):
    def test_first_acquire_succeeds_and_is_visible(self):
        registry = MarginModeSymbolRegistry()
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        self.assertEqual(registry.owner_of("BTCUSDT"), ("bot-1", "ISOLATED"))

    def test_same_owner_reacquiring_same_mode_is_idempotent(self):
        registry = MarginModeSymbolRegistry()
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        self.assertEqual(registry.owner_of("BTCUSDT"), ("bot-1", "ISOLATED"))

    def test_different_owner_same_symbol_is_locked(self):
        registry = MarginModeSymbolRegistry()
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        with self.assertRaises(MarginModeRegistryError) as ctx:
            registry.acquire("BTCUSDT", "bot-2", "ISOLATED")
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_SYMBOL_LOCKED")

    def test_same_owner_conflicting_mode_is_rejected(self):
        registry = MarginModeSymbolRegistry()
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        with self.assertRaises(MarginModeRegistryError) as ctx:
            registry.acquire("BTCUSDT", "bot-1", "CROSS")
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_OWNER_MODE_CONFLICT")

    def test_different_symbols_are_independent(self):
        registry = MarginModeSymbolRegistry()
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        registry.acquire("ETHUSDT", "bot-2", "CROSS")
        self.assertEqual(registry.owner_of("BTCUSDT"), ("bot-1", "ISOLATED"))
        self.assertEqual(registry.owner_of("ETHUSDT"), ("bot-2", "CROSS"))

    def test_release_frees_the_symbol_for_a_new_owner(self):
        registry = MarginModeSymbolRegistry()
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        registry.release("BTCUSDT", "bot-1")
        self.assertIsNone(registry.owner_of("BTCUSDT"))
        registry.acquire("BTCUSDT", "bot-2", "CROSS")
        self.assertEqual(registry.owner_of("BTCUSDT"), ("bot-2", "CROSS"))

    def test_release_by_non_owner_is_rejected(self):
        registry = MarginModeSymbolRegistry()
        registry.acquire("BTCUSDT", "bot-1", "ISOLATED")
        with self.assertRaises(MarginModeRegistryError) as ctx:
            registry.release("BTCUSDT", "bot-2")
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_RELEASE_NOT_OWNER")

    def test_release_of_unowned_symbol_is_rejected(self):
        registry = MarginModeSymbolRegistry()
        with self.assertRaises(MarginModeRegistryError):
            registry.release("BTCUSDT", "bot-1")

    def test_invalid_mode_is_rejected(self):
        registry = MarginModeSymbolRegistry()
        with self.assertRaises(MarginModeRegistryError) as ctx:
            registry.acquire("BTCUSDT", "bot-1", "SPOT")
        self.assertEqual(ctx.exception.code, "MARGIN_MODE_INVALID")


if __name__ == "__main__":
    unittest.main()
