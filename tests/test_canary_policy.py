import json
import tempfile
import unittest
from pathlib import Path

from check_workspace import ROOT

from dcabot.application.canary_policy import (
    CanaryObservations,
    CanarySpec,
    disengage_kill_switch,
    engage_kill_switch,
    evaluate_canary,
    read_kill_switch,
)


def _spec(**overrides):
    base = {
        "status": "ACTIVE",
        "amount_cap_quote": "100",
        "daily_loss_limit_quote": "10",
        "starts_at": "2026-09-21T00:00:00+00:00",
        "ends_at": "2026-09-28T00:00:00+00:00",
        "min_trades": 5,
    }
    base.update(overrides)
    return CanarySpec(**base)


def _obs(**overrides):
    base = {
        "trade_count": 5,
        "duplicate_count": 0,
        "unresolved_unknown_count": 0,
        "realized_pnl_quote": "1.5",
        "now": "2026-09-22T00:00:00+00:00",
        "kill_switch_engaged": False,
    }
    base.update(overrides)
    return CanaryObservations(**base)


class CanaryPolicyTests(unittest.TestCase):
    def test_healthy_window_returns_go(self):
        verdict = evaluate_canary(_spec(), _obs())

        self.assertEqual(verdict.verdict, "CANARY_GO")
        self.assertEqual(verdict.reasons, ())

    def test_draft_spec_never_goes(self):
        verdict = evaluate_canary(_spec(status="DRAFT"), _obs())

        self.assertEqual(verdict.verdict, "CANARY_NOGO")
        self.assertIn("SPEC_NOT_ACTIVE", verdict.reasons)

    def test_kill_switch_forces_nogo(self):
        verdict = evaluate_canary(_spec(), _obs(kill_switch_engaged=True))

        self.assertEqual(verdict.verdict, "CANARY_NOGO")
        self.assertIn("KILL_SWITCH_ENGAGED", verdict.reasons)

    def test_outside_window_forces_nogo(self):
        before = evaluate_canary(_spec(), _obs(now="2026-09-20T00:00:00+00:00"))
        after = evaluate_canary(_spec(), _obs(now="2026-09-29T00:00:00+00:00"))

        self.assertEqual(before.verdict, "CANARY_NOGO")
        self.assertIn("OUTSIDE_WINDOW", before.reasons)
        self.assertEqual(after.verdict, "CANARY_NOGO")
        self.assertIn("OUTSIDE_WINDOW", after.reasons)

    def test_any_duplicate_or_unresolved_unknown_forces_nogo(self):
        dup = evaluate_canary(_spec(), _obs(duplicate_count=1))
        unknown = evaluate_canary(_spec(), _obs(unresolved_unknown_count=1))

        self.assertIn("DUPLICATE_DETECTED", dup.reasons)
        self.assertIn("UNRESOLVED_UNKNOWN", unknown.reasons)

    def test_loss_beyond_limit_forces_nogo_exact_boundary(self):
        at_limit = evaluate_canary(_spec(), _obs(realized_pnl_quote="-10"))
        beyond = evaluate_canary(_spec(), _obs(realized_pnl_quote="-10.000000000001"))

        self.assertEqual(at_limit.verdict, "CANARY_GO")
        self.assertEqual(beyond.verdict, "CANARY_NOGO")
        self.assertIn("DAILY_LOSS_EXCEEDED", beyond.reasons)

    def test_below_minimum_trades_forces_nogo(self):
        verdict = evaluate_canary(_spec(), _obs(trade_count=4))

        self.assertEqual(verdict.verdict, "CANARY_NOGO")
        self.assertIn("BELOW_MINIMUM_TRADES", verdict.reasons)

    def test_invalid_observation_fails_closed(self):
        verdict = evaluate_canary(_spec(), _obs(realized_pnl_quote="NaN"))

        self.assertEqual(verdict.verdict, "CANARY_NOGO")
        self.assertIn("INVALID_OBSERVATION", verdict.reasons)

    def test_shipped_canary_file_parses_and_stays_draft_closed(self):
        raw = json.loads((ROOT / "config/canary.json").read_text(encoding="utf-8"))
        raw.pop("_note", None)
        spec = CanarySpec(**raw)

        self.assertEqual(spec.status, "DRAFT")
        verdict = evaluate_canary(spec, _obs())
        self.assertEqual(verdict.verdict, "CANARY_NOGO")
        self.assertIn("SPEC_NOT_ACTIVE", verdict.reasons)

    def test_invalid_spec_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            _spec(amount_cap_quote="-5")
        with self.assertRaises(ValueError):
            _spec(ends_at="2026-09-20T00:00:00+00:00")
        with self.assertRaises(ValueError):
            _spec(min_trades=0)


class KillSwitchFileTests(unittest.TestCase):
    def test_missing_file_means_disengaged(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(read_kill_switch(Path(td) / "kill_switch.json"))

    def test_corrupt_file_fails_closed_to_engaged(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "kill_switch.json"
            path.write_text("{not json", encoding="utf-8")
            self.assertTrue(read_kill_switch(path))

    def test_engage_disengage_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "kill_switch.json"
            engage_kill_switch(path, "manual stop")
            self.assertTrue(read_kill_switch(path))
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["reason"], "manual stop")
            disengage_kill_switch(path)
            self.assertFalse(read_kill_switch(path))
