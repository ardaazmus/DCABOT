import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from fractions import Fraction as F
from concurrent.futures import ThreadPoolExecutor
from check_workspace import ROOT
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, decision, report
from dcabot.application.service import preview, notional, replay, replay_tick
from dcabot.persistence.store import (
    Conflict,
    LedgerInvariantError,
    Store,
    _require_balanced_postings,
)


def raw(**updates):
    c = json.loads((ROOT / "config/paper.json").read_text())
    c.update(updates)
    return c


def intent(oid="base", role="BASE", qty="1", price="100"):
    return {
        "type": "INTENT",
        "order_id": oid,
        "role": role,
        "qty": qty,
        "limit_price": price,
    }


def fill(eid="exec1", oid="base", side="BUY", qty="1", price="100", fee="0.1"):
    return {
        "type": "FILL",
        "execution_id": eid,
        "order_id": oid,
        "side": side,
        "qty": qty,
        "price": price,
        "fee": fee,
        "fee_asset": "USDT",
    }


def final(oid="base", qty="1", status="FILLED", complete=True):
    return {
        "type": "ORDER_FINAL",
        "order_id": oid,
        "status": status,
        "filled_qty": qty,
        "coverage_complete": complete,
    }


class EngineTests(unittest.TestCase):
    def test_ladder_preview_and_unit_boundary(self):
        out = preview(raw(safety_count=3), "100")
        self.assertEqual([x["price"] for x in out["levels"]], ["90", "80", "70"])
        self.assertEqual(out["planned_gross_notional"], "340")
        self.assertIsNone(out["policy_required_collateral"])
        with self.assertRaises(ValueError):
            preview(raw(safety_count=10), "100")
        with self.assertRaises(ValueError):
            preview(raw(tick="10", deviation="0.001"), "100")
        fixture = json.loads((ROOT / "tests/fixtures/notional.json").read_text())
        self.assertEqual(notional(fixture)["notional"], "4.01")
        fixture["qty_asset"] = "USDT"
        with self.assertRaises(ValueError):
            notional(fixture)

    def test_preview_uses_executable_base_price_for_cap_and_plan(self):
        out = preview(
            raw(safety_count=0, tick="1", max_entry_notional="100.5"),
            "100.1",
        )

        self.assertEqual(out["anchor"], "101")
        self.assertEqual(out["base_notional"], "101")
        self.assertEqual(out["planned_gross_notional"], "101")
        self.assertFalse(out["within_gross_entry_cap"])

    def test_intent_and_status_do_not_manufacture_fills(self):
        c = Config.parse(raw())
        s = apply(State(), {"type": "MARK", "price": "100"}, c)
        s = apply(s, intent(), c)
        self.assertEqual(s.position.qty, 0)
        s = apply(s, final(), c)
        self.assertIsNone(s.anchor)
        self.assertEqual(s.orders["base"].status, "UNKNOWN")
        self.assertIsNone(decision(s, c))

    def test_partial_base_cannot_start_safety_without_final_coverage(self):
        c = Config.parse(raw())
        s = State()
        for e in (
            {"type": "MARK", "price": "100"},
            intent(),
            fill(qty="0.5", fee="0.05"),
            {"type": "MARK", "price": "80"},
        ):
            s = apply(s, e, c)
        self.assertIsNone(s.anchor)
        self.assertIsNone(decision(s, c))
        s = apply(s, final(qty="0.5", status="CANCELED"), c)
        self.assertEqual(s.anchor, 100)
        self.assertEqual(decision(s, c), ("SAFETY:1", F(1)))

    def test_partial_fill_exposes_conserved_order_state_until_explicit_cancel(self):
        c = Config.parse(raw())
        s = apply(State(), {"type": "MARK", "price": "100"}, c)
        s = apply(s, intent(), c)
        s = apply(s, fill(qty="0.4", fee="0.04"), c)

        self.assertEqual(
            (
                s.orders["base"].status,
                s.orders["base"].leaves,
                s.orders["base"].canceled,
            ),
            ("PARTIALLY_FILLED", F(3, 5), F(0)),
        )

        s = apply(s, final(qty="0.4", status="CANCELED"), c)

        self.assertEqual(
            (
                s.orders["base"].status,
                s.orders["base"].leaves,
                s.orders["base"].canceled,
                s.position.qty,
            ),
            ("CANCELED", F(0), F(3, 5), F(2, 5)),
        )

    def test_partial_canceled_safety_stops_ladder(self):
        c = Config.parse(raw())
        s = State()
        events = [
            {"type": "MARK", "price": "100"},
            intent(),
            fill(),
            final(),
            {"type": "MARK", "price": "90"},
            intent("s1", "SAFETY:1", "1", "90"),
            fill("e2", "s1", qty="0.5", price="90", fee="0.045"),
            final("s1", "0.5", "CANCELED"),
            {"type": "MARK", "price": "70"},
        ]
        for e in events:
            s = apply(s, e, c)
        self.assertTrue(s.safety_stopped)
        self.assertIsNone(decision(s, c))
        self.assertEqual(s.position.qty, F(3, 2))

    def test_drawdown_latches_and_proposes_protective_exit(self):
        c = Config.parse(
            raw(
                initial_equity="100",
                minimum_equity="1",
                base_qty="0.5",
                max_drawdown="0.15",
            )
        )
        s = State()
        for e in (
            {"type": "MARK", "price": "100"},
            intent(qty="0.5"),
            fill(qty="0.5", fee="0"),
            final(qty="0.5"),
            {"type": "MARK", "price": "140"},
            {"type": "MARK", "price": "100"},
        ):
            s = apply(s, e, c)
        self.assertEqual(s.max_dd, F(1, 6))
        self.assertTrue(s.halted)
        self.assertEqual(decision(s, c), ("STOP", F(1, 2)))
        s = apply(s, {"type": "MARK", "price": "150"}, c)
        self.assertTrue(s.halted)

    def test_unknown_and_insufficient_coverage_block_repetition(self):
        c = Config.parse(raw())
        s = State()
        for e in (
            {"type": "MARK", "price": "100"},
            intent(),
            {"type": "UNKNOWN", "order_id": "base"},
            final(qty="0", status="CANCELED", complete=False),
        ):
            s = apply(s, e, c)
        self.assertIsNone(decision(s, c))
        self.assertEqual(s.position.qty, 0)
        with self.assertRaises(ValueError):
            apply(s, intent("retry"), c)

    def test_config_rejects_scope_expansion_and_inexact_order_grid(self):
        for updates in (
            {"mode": "mainnet"},
            {"safety_count": True},
            {"base_qty": "0.0005"},
            {"max_drawdown": "1"},
            {"fee_rate": "1"},
            {"quote_asset": "BTC"},
            {"base_qty": 1.0},
        ):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                Config.parse(raw(**updates))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "paper.db"
        self.store = Store(self.path, raw())

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def seed(self):
        self.store.append("m", {"type": "MARK", "price": "100"})
        self.store.append("i", intent())

    def test_duplicate_execution_with_different_transport_id_has_one_effect(self):
        self.seed()
        self.store.append("f", fill())
        self.store.append("another-message", fill())
        self.assertEqual(self.store.load().position.qty, 1)
        self.assertEqual(self.store.load().fees, F(1, 10))
        self.assertEqual(self.store.audit()["events"], 3)

    def test_conflicting_execution_is_quarantined_and_blocks_new_risk(self):
        self.seed()
        self.store.append("f", fill())
        with self.assertRaises(Conflict):
            self.store.append("f2", fill(price="99"))
        s = self.store.load()
        self.assertEqual(s.position.cost, 100)
        self.assertIn("PERSISTENT_INCIDENT_REQUIRES_REVIEW", s.blockers)
        self.assertEqual(self.store.audit()["incidents"], 1)

    def test_overfill_preserves_raw_incident_without_false_position(self):
        self.seed()
        with self.assertRaises(ValueError):
            self.store.append("over", fill(qty="2"))
        self.assertEqual(self.store.load().position.qty, 0)
        self.assertEqual(self.store.audit()["incidents"], 1)
        self.assertIn(
            '"qty":"2"',
            self.store.db.execute("SELECT request FROM incidents").fetchone()[0],
        )

    def test_posting_failure_rolls_back_execution_and_can_retry(self):
        self.seed()
        self.store.db.execute(
            "CREATE TRIGGER fail_post BEFORE INSERT ON postings BEGIN SELECT RAISE(ABORT,'injected'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.append("f", fill())
        self.assertEqual(self.store.load().position.qty, 0)
        self.assertEqual(self.store.audit()["events"], 2)
        self.store.db.execute("DROP TRIGGER fail_post")
        self.store.append("f", fill())
        self.assertEqual(self.store.load().position.qty, 1)

    def test_unbalanced_postings_raise_without_assertions(self):
        with self.assertRaises(LedgerInvariantError):
            _require_balanced_postings({"WALLET": F(1), "REALIZED_PNL": F(0)})

    def test_restart_rebuilds_exact_partial_position_and_postings(self):
        events = [
            {"type": "MARK", "price": "100"},
            intent(),
            fill(),
            final(),
            {"type": "MARK", "price": "90"},
            intent("s1", "SAFETY:1", "1", "90"),
            fill("e2", "s1", price="90", fee="0.09"),
            final("s1"),
            {"type": "MARK", "price": "110"},
            intent("exit", "EXIT", "0.5", "110"),
            fill("e3", "exit", "SELL", "0.5", "110", "0.055"),
            final("exit", "0.5"),
            {"type": "FUNDING", "amount": "0.2", "asset": "USDT"},
            {"type": "MARK", "price": "100"},
        ]
        for i, event in enumerate(events):
            self.store.append(f"event:{i}", event)
        before = report(self.store.load(), self.store.config)
        with Store(self.path) as reopened:
            after = report(reopened.load(), reopened.config)
            self.assertEqual(before, after)
            self.assertEqual(after["equity"], "1014.555")
            self.assertEqual(after["average"], "95")
            self.assertEqual(reopened.audit()["status"], "PASS")

    def test_replay_known_cycle_repeat_and_restart(self):
        ticks = json.loads((ROOT / "tests/fixtures/demo_ticks.json").read_text())
        replay(self.store, ticks[:2])
        with Store(self.path) as resumed:
            out = replay(resumed, ticks)
            self.assertEqual(out["equity"], "1029.43")
            self.assertEqual(out["fees"], "0.57")
            self.assertEqual(out["realized_gross"], "30")
            self.assertEqual(out["qty"], "0")
            self.assertEqual(out["max_drawdown"], "0.03027")
            self.assertTrue(out["deal_complete"])
            self.assertEqual(out, replay(resumed, ticks))
            self.assertEqual(out["audit"]["events"], 16)

    def test_tick_failure_rolls_back_whole_synthetic_cycle(self):
        self.store.db.execute(
            "CREATE TRIGGER fail_fill BEFORE INSERT ON events WHEN NEW.execution_id IS NOT NULL BEGIN SELECT RAISE(ABORT,'injected'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            replay_tick(self.store, "tick", "100")
        self.assertEqual(self.store.audit()["events"], 0)
        self.store.db.execute("DROP TRIGGER fail_fill")
        replay_tick(self.store, "tick", "100")
        self.assertEqual(self.store.audit()["events"], 4)

    def test_two_writers_cannot_both_reserve_the_next_order(self):
        self.store.append("mark", {"type": "MARK", "price": "100"})

        def attempt(i):
            with Store(self.path) as db:
                try:
                    db.append(f"intent:{i}", intent(f"order:{i}"))
                    return True
                except ValueError:
                    return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(len(self.store.load().orders), 1)

    def test_existing_unrelated_database_is_never_overwritten(self):
        other = Path(self.temp.name) / "foreign.db"
        db = sqlite3.connect(other)
        db.execute("CREATE TABLE important(value)")
        db.commit()
        db.close()
        original = other.read_bytes()
        with self.assertRaises(FileExistsError):
            Store(other, raw())
        with self.assertRaises(ValueError):
            Store(other)
        self.assertEqual(other.read_bytes(), original)

    def test_tampered_posting_is_detected_on_open(self):
        self.seed()
        self.store.append("fill", fill())
        self.store.db.execute(
            "UPDATE postings SET numerator='999' WHERE account='FEE_EXPENSE'"
        )
        with self.assertRaises(Conflict):
            Store(self.path)

    def test_real_process_death_rolls_back_uncommitted_batch(self):
        script = """
import os,sys
from pathlib import Path
from dcabot.persistence.store import Store
with Store(Path(sys.argv[1])) as db:
    def crash(state,emit):
        emit({'type':'MARK','price':'100'})
        os._exit(17)
    db.transact('crash',{'type':'test'},crash)
"""
        import os

        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        result = subprocess.run(
            [sys.executable, "-c", script, str(self.path)], env=env, capture_output=True
        )
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(self.store.audit()["events"], 0)
        self.assertTrue(self.store.append("crash", {"type": "MARK", "price": "100"}))

    def test_policy_rejection_is_durable_and_visible(self):
        small = Path(self.temp.name) / "small.db"
        with Store(small, raw(max_entry_notional="50")) as db:
            replay_tick(db, "small", "100")
            s = db.load()
            self.assertEqual(s.position.qty, 0)
            self.assertEqual(s.last_rejection, "Gross entry notional cap exceeded")
            self.assertEqual(db.audit()["events"], 2)


class ReplayBoundaryTests(unittest.TestCase):
    def test_gap_produces_only_one_safety_per_tick(self):
        with tempfile.TemporaryDirectory() as td, Store(Path(td) / "x.db", raw()) as db:
            replay_tick(db, "one", "100")
            replay_tick(db, "two", "70")
            self.assertEqual(db.load().position.qty, 2)
            self.assertEqual(len(db.load().orders), 2)
            replay_tick(db, "three", "70")
            self.assertEqual(db.load().position.qty, 3)

    def test_slippage_changes_execution_price_once(self):
        with (
            tempfile.TemporaryDirectory() as td,
            Store(Path(td) / "x.db", raw(slippage="0.01")) as db,
        ):
            out = replay(
                db, json.loads((ROOT / "tests/fixtures/demo_ticks.json").read_text())
            )
            self.assertEqual(out["realized_gross"], "24.3")
            self.assertEqual(out["fees"], "0.5697")
            self.assertEqual(out["equity"], "1023.7303")

    def test_late_fill_is_accounted_but_invalidates_coverage(self):
        with tempfile.TemporaryDirectory() as td, Store(Path(td) / "x.db", raw()) as db:
            for i, e in enumerate(
                [
                    {"type": "MARK", "price": "100"},
                    intent(),
                    final(qty="0", status="CANCELED"),
                    fill(qty="0.5", fee="0.05"),
                ]
            ):
                db.append(f"late:{i}", e)
            s = db.load()
            self.assertEqual(s.position.qty, F(1, 2))
            self.assertIn("LATE_FILL_AFTER_FINAL", s.blockers)
            self.assertEqual(s.orders["base"].status, "UNKNOWN")
            self.assertEqual(db.audit()["status"], "PASS")

    def test_funding_receipt_and_fee_rebate_increase_equity(self):
        with tempfile.TemporaryDirectory() as td, Store(Path(td) / "x.db", raw()) as db:
            for i, e in enumerate(
                [
                    {"type": "MARK", "price": "100"},
                    intent(),
                    fill(fee="-0.01"),
                    final(),
                    {"type": "FUNDING", "amount": "-0.2", "asset": "USDT"},
                ]
            ):
                db.append(f"credit:{i}", e)
            self.assertEqual(db.load().equity(db.config), F(100021, 100))
            self.assertEqual(db.audit()["status"], "PASS")
