import unittest

from dcabot.application.paper_trading_gate import (
    PaperSession,
    PaperTradingGateError,
    activate_paper_session,
)


def _activate(**overrides):
    params = {
        "confirmed": True,
        "session_time_us": 1700000000000000,
        "symbols": ("BTCUSDT",),
        "max_staleness_us": 5_000_000,
        "starting_cash": "10000",
        "credential_present": False,
    }
    params.update(overrides)
    return activate_paper_session(**params)


class ActivatePaperSessionTests(unittest.TestCase):
    def test_confirmed_activation_returns_deterministic_session(self):
        first = _activate()
        second = _activate()
        self.assertIsInstance(first, PaperSession)
        self.assertEqual(first.status, "PAPER_ACTIVE")
        self.assertEqual(first.symbols, ("BTCUSDT",))
        self.assertEqual(first.cash, "10000")
        self.assertEqual(first.positions, ())
        self.assertEqual(first.orders, ())
        self.assertEqual(first.session_id, second.session_id)
        self.assertRegex(first.session_id, r"\A[0-9a-f]{64}\Z")

    def test_session_id_changes_with_config(self):
        base = _activate()
        other = _activate(starting_cash="10001")
        self.assertNotEqual(base.session_id, other.session_id)

    def test_unconfirmed_activation_is_rejected(self):
        with self.assertRaises(PaperTradingGateError) as ctx:
            _activate(confirmed=False)
        self.assertEqual(ctx.exception.code, "PAPER_ACTIVATION_NOT_CONFIRMED")

    def test_non_boolean_confirmation_is_rejected(self):
        with self.assertRaises(PaperTradingGateError) as ctx:
            _activate(confirmed="yes")
        self.assertEqual(ctx.exception.code, "PAPER_ACTIVATION_NOT_CONFIRMED")

    def test_credential_presence_forbids_paper_session(self):
        with self.assertRaises(PaperTradingGateError) as ctx:
            _activate(credential_present=True)
        self.assertEqual(ctx.exception.code, "PAPER_CREDENTIAL_FORBIDDEN")

    def test_empty_symbols_rejected(self):
        with self.assertRaises(PaperTradingGateError) as ctx:
            _activate(symbols=())
        self.assertEqual(ctx.exception.code, "PAPER_SYMBOLS_INVALID")

    def test_duplicate_symbols_rejected(self):
        with self.assertRaises(PaperTradingGateError) as ctx:
            _activate(symbols=("BTCUSDT", "BTCUSDT"))
        self.assertEqual(ctx.exception.code, "PAPER_SYMBOLS_DUPLICATE")

    def test_zero_cash_rejected(self):
        with self.assertRaises(PaperTradingGateError) as ctx:
            _activate(starting_cash="0")
        self.assertEqual(ctx.exception.code, "PAPER_CASH_INVALID")

    def test_bool_time_rejected(self):
        with self.assertRaises(PaperTradingGateError) as ctx:
            _activate(session_time_us=True)
        self.assertEqual(ctx.exception.code, "PAPER_TIME_INVALID")


if __name__ == "__main__":
    unittest.main()
