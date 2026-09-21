import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from dcabot.application.canary_policy import CanaryObservations, CanarySpec
from dcabot.application.live_gate import (
    LiveTradingBlocked,
    assert_live_trading_allowed,
)


def _active_spec():
    return CanarySpec(
        status="ACTIVE",
        amount_cap_quote="100",
        daily_loss_limit_quote="10",
        starts_at="2026-09-21T00:00:00+00:00",
        ends_at="2026-09-28T00:00:00+00:00",
        min_trades=5,
    )


def _healthy_obs():
    return CanaryObservations(
        trade_count=5,
        duplicate_count=0,
        unresolved_unknown_count=0,
        realized_pnl_quote="1.5",
        now="2026-09-22T00:00:00+00:00",
        kill_switch_engaged=False,
    )


class LiveGateTests(unittest.TestCase):
    def test_closed_without_approval_even_when_policy_is_go(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(LiveTradingBlocked) as ctx:
                assert_live_trading_allowed(
                    spec=_active_spec(),
                    obs=_healthy_obs(),
                    approval_path=Path(td) / "approval.json",
                    kill_switch_path=Path(td) / "kill_switch.json",
                )
            self.assertIn("CANARY_APPROVAL_MISSING", ctx.exception.reasons)

    def test_kill_switch_file_blocks_even_with_approval_present(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "approval.json").write_text('{"approved_by": "x"}', encoding="utf-8")
            (root / "kill_switch.json").write_text(
                '{"engaged": true, "reason": "stop"}', encoding="utf-8"
            )
            with self.assertRaises(LiveTradingBlocked) as ctx:
                assert_live_trading_allowed(
                    spec=_active_spec(),
                    obs=_healthy_obs(),
                    approval_path=root / "approval.json",
                    kill_switch_path=root / "kill_switch.json",
                )
            self.assertIn("KILL_SWITCH_ENGAGED", ctx.exception.reasons)

    def test_policy_nogo_blocks_with_policy_reasons(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "approval.json").write_text('{"approved_by": "x"}', encoding="utf-8")
            bad_obs = replace(_healthy_obs(), duplicate_count=1)
            with self.assertRaises(LiveTradingBlocked) as ctx:
                assert_live_trading_allowed(
                    spec=_active_spec(),
                    obs=bad_obs,
                    approval_path=root / "approval.json",
                    kill_switch_path=root / "kill_switch.json",
                )
            self.assertIn("DUPLICATE_DETECTED", ctx.exception.reasons)
