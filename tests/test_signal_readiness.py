import unittest

from dcabot.application.signal_event_contract import new_signal_event
from dcabot.application.signal_readiness import (
    SignalReadinessError,
    assess_signal_readiness,
)


def signal(*, event_time_us=1_000):
    return new_signal_event(
        signal_id="sig-1",
        source="offline-fixture",
        event_time_us=event_time_us,
        schema_version="signal-v1",
        payload_hash="a" * 64,
    )


class SignalReadinessTests(unittest.TestCase):
    def test_incomplete_warmup_is_not_ready(self):
        result = assess_signal_readiness(
            signal(),
            closed_bar_time_us=1_000,
            warmup_bars_observed=4,
            required_warmup_bars=5,
            max_staleness_us=0,
        )

        self.assertEqual(result.status, "WARMING_UP")

    def test_incomplete_bar_is_never_consumed_as_closed(self):
        result = assess_signal_readiness(
            signal(event_time_us=1_001),
            closed_bar_time_us=1_000,
            warmup_bars_observed=5,
            required_warmup_bars=5,
            max_staleness_us=10,
        )

        self.assertEqual(result.status, "WAITING_FOR_CLOSED_BAR")

    def test_stale_signal_is_explicitly_blocked(self):
        result = assess_signal_readiness(
            signal(event_time_us=1_000),
            closed_bar_time_us=2_000,
            warmup_bars_observed=5,
            required_warmup_bars=5,
            max_staleness_us=999,
        )

        self.assertEqual(result.status, "STALE")

    def test_stale_boundary_is_still_acceptable(self):
        result = assess_signal_readiness(
            signal(event_time_us=1_500),
            closed_bar_time_us=2_000,
            warmup_bars_observed=5,
            required_warmup_bars=5,
            max_staleness_us=500,
        )

        self.assertEqual(result.status, "READY")

    def test_ready_signal_is_a_gate_only(self):
        result = assess_signal_readiness(
            signal(event_time_us=1_500),
            closed_bar_time_us=2_000,
            warmup_bars_observed=5,
            required_warmup_bars=5,
            max_staleness_us=500,
        )

        self.assertEqual(result.status, "READY")
        self.assertFalse(hasattr(result, "orders"))
        self.assertFalse(hasattr(result, "fills"))

    def test_invalid_gate_inputs_fail_closed(self):
        cases = (
            {"closed_bar_time_us": True},
            {"warmup_bars_observed": True},
            {"required_warmup_bars": True},
            {"max_staleness_us": True},
            {"warmup_bars_observed": -1},
            {"required_warmup_bars": 0},
            {"max_staleness_us": -1},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides), self.assertRaises(
                SignalReadinessError
            ):
                values = {
                    "closed_bar_time_us": 1_000,
                    "warmup_bars_observed": 5,
                    "required_warmup_bars": 5,
                    "max_staleness_us": 0,
                }
                values.update(overrides)
                assess_signal_readiness(signal(), **values)
