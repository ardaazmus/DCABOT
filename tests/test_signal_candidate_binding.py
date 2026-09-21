import unittest

from dcabot.application.signal_candidate_binding import (
    SignalCandidateBindingError,
    bind_signal_candidate,
)
from dcabot.application.signal_event_contract import new_signal_event
from dcabot.application.signal_readiness import assess_signal_readiness

HASH = "6d5092a32c7977230e61f3569261e2ae1735096f5896a550a6d1e8b98a9c6cec"
MAP = (("BUY", "BUY"), ("SELL", "SELL"), ("LONG", "BUY"), ("SHORT", "SELL"))


def _signal():
    return new_signal_event(
        signal_id="s1",
        source="offline-fixture",
        event_time_us=1700000000000000,
        schema_version="signal-v1",
        payload_hash=HASH,
    )


def _readiness(signal=None, **overrides):
    params = {
        "closed_bar_time_us": 1700000000000000,
        "warmup_bars_observed": 10,
        "required_warmup_bars": 5,
        "max_staleness_us": 5_000_000,
    }
    params.update(overrides)
    return assess_signal_readiness(signal or _signal(), **params)


def _bind(**overrides):
    params = {
        "signal": _signal(),
        "readiness": _readiness(),
        "action": "BUY",
        "symbol": "BTCUSDT",
        "action_map": MAP,
        "qty": "0.01",
        "ttl_us": 60_000_000,
        "binding_time_us": 1700000002000000,
    }
    params.update(overrides)
    return bind_signal_candidate(**params)


class BindSignalCandidateTests(unittest.TestCase):
    def test_ready_signal_binds_deterministic_candidate(self):
        first = _bind()
        second = _bind()
        self.assertEqual(first.status, "CANDIDATE")
        self.assertEqual(first.signal_id, "s1")
        self.assertEqual(first.payload_hash, HASH)
        self.assertEqual(first.symbol, "BTCUSDT")
        self.assertEqual(first.side, "BUY")
        self.assertEqual(first.qty, "0.01")
        self.assertEqual(first.expires_us, 1700000060000000)
        self.assertEqual(first.candidate_id, second.candidate_id)
        self.assertRegex(first.candidate_id, r"\A[0-9a-f]{64}\Z")

    def test_candidate_id_changes_with_qty(self):
        self.assertNotEqual(_bind().candidate_id, _bind(qty="0.02").candidate_id)

    def test_mapped_alias_resolves_side(self):
        candidate = _bind(action="SHORT")
        self.assertEqual(candidate.side, "SELL")

    def test_not_ready_assessment_rejected(self):
        warming = _readiness(warmup_bars_observed=2)
        self.assertEqual(warming.status, "WARMING_UP")
        with self.assertRaises(SignalCandidateBindingError) as ctx:
            _bind(readiness=warming)
        self.assertEqual(ctx.exception.code, "SIGNAL_CANDIDATE_NOT_READY")

    def test_assessment_for_other_signal_rejected(self):
        other = new_signal_event(
            signal_id="s2",
            source="offline-fixture",
            event_time_us=1700000000000000,
            schema_version="signal-v1",
            payload_hash=HASH,
        )
        with self.assertRaises(SignalCandidateBindingError) as ctx:
            _bind(readiness=_readiness(other))
        self.assertEqual(ctx.exception.code, "SIGNAL_CANDIDATE_ASSESSMENT_MISMATCH")

    def test_unmapped_action_rejected(self):
        with self.assertRaises(SignalCandidateBindingError) as ctx:
            _bind(action="HOLD")
        self.assertEqual(ctx.exception.code, "SIGNAL_CANDIDATE_ACTION_UNMAPPED")

    def test_bad_symbol_rejected(self):
        with self.assertRaises(SignalCandidateBindingError) as ctx:
            _bind(symbol="BTC USDT")
        self.assertEqual(ctx.exception.code, "SIGNAL_CANDIDATE_SYMBOL_INVALID")

    def test_bad_qty_rejected(self):
        with self.assertRaises(SignalCandidateBindingError) as ctx:
            _bind(qty="0")
        self.assertEqual(ctx.exception.code, "SIGNAL_CANDIDATE_QTY_INVALID")

    def test_zero_ttl_rejected(self):
        with self.assertRaises(SignalCandidateBindingError) as ctx:
            _bind(ttl_us=0)
        self.assertEqual(ctx.exception.code, "SIGNAL_CANDIDATE_TTL_INVALID")


if __name__ == "__main__":
    unittest.main()
