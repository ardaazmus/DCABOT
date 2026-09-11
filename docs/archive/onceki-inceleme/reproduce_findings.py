"""Read-only, offline probes against a supplied DCABOT checkout. No pytest required.

Exit 0 means probes ran; BUG_REPRODUCED is not a product test pass.
Usage: python reproduce_findings.py /path/to/DCABOT
"""
import json
import platform
import sys
import tempfile
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "src"))
from dcabot.domain.dca_math import calculate_dca_ladder
from dcabot.domain.liquidation import compute_liquidation_price
from dcabot.domain.reconciliation import OrderSnapshot, reconcile_orders
from dcabot.replay.dca_strategy import DcaStrategy
from dcabot.replay.multi_pair_orchestrator import MultiPairOrchestrator
from dcabot.server.daemon import PidLock
from dcabot.server.recovery import ServerStateSnapshot, plan_startup_recovery

results = []
def record(key, observed, expected, bug):
    results.append(dict(id=key, status="BUG_REPRODUCED" if bug else "NOT_REPRODUCED",
                        observed=observed, corrected_contract=expected))

liq = compute_liquidation_price(entry_price=D("100"), leverage=10, side="LONG", mmr=D("0.005"))
root_price = (D("100") - D("10")) / (D("1") - D("0.005"))
record("F01", str(liq), "Toy root 90/0.995=" + str(root_price) + "; not exchange-exact", liq != root_price)

ladder = calculate_dca_ladder(base_price=D("100"), base_amount=D("1"), safety_amount=D("1"),
                             max_so=2, price_deviation_pct=D("0.6"), volume_scale=D("1"),
                             step_scale=D("1"), tp_pct=D("0.02"))
record("F03", str(ladder.steps[-1].target_price), "Reject deviation >= 1; do not invent price", ladder.steps[-1].target_price == D("0.00000001"))

order = OrderSnapshot(order_id="o1", symbol="BTCUSDT", side="BUY", price=D("100"),
                      quantity=D("1"), filled_quantity=D("0"), status="NEW")
snap = ServerStateSnapshot(timestamp_ms=0, active_bots=("b1",), total_reserved_equity=D("100"), orders=(order,))
recovery = plan_startup_recovery(snap, {})
record("F05", dict(safe=recovery.is_safe_to_resume, actions=list(recovery.actions)),
       "Missing in unknown query scope => unresolved; no cancellation inference or new-risk resume", recovery.is_safe_to_resume)

report = reconcile_orders(local_orders={"o1": order}, venue_orders={"o1": replace(order, status="CANCELED")})
record("F06", dict(clean=report.is_clean, discrepancies=len(report.discrepancies)),
       "NEW versus CANCELED must be a status discrepancy", report.is_clean)

strategy = DcaStrategy(symbol="BTCUSDT", base_order_qty=D("1"), safety_order_qty=D("1"),
                       max_safety_orders=1, price_deviation_pct=D("0.1"))
orch = MultiPairOrchestrator(total_equity=D("100"), max_portfolio_dd_pct=D("0.15"))
orch.register_bot(bot_id="b", symbol="BTCUSDT", strategy=strategy)
orch.try_reserve_margin(bot_id="b", required_margin=D("10"))
orch.settle_deal(bot_id="b", released_margin=D("10"), net_realized_pnl=D("20"))
orch.settle_deal(bot_id="b", released_margin=D("10"), net_realized_pnl=D("20"))
record("F07", str(orch.total_equity), "Same settlement identity posted once => 120", orch.total_equity == D("140"))

dd = MultiPairOrchestrator(total_equity=D("100"), max_portfolio_dd_pct=D("0.15"))
dd.register_bot(bot_id="b", symbol="BTCUSDT", strategy=strategy)
dd.settle_deal(bot_id="b", released_margin=D("0"), net_realized_pnl=D("20"))
dd.settle_deal(bot_id="b", released_margin=D("0"), net_realized_pnl=D("-20"))
record("F08", dict(equity=str(dd.total_equity), tripped=dd.is_circuit_tripped),
       "100 -> 120 -> 100 peak drawdown = 1/6; crosses 15%", not dd.is_circuit_tripped)

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "lock"
    owner = PidLock(path)
    other = PidLock(path)
    owner.acquire(pid=101)
    other.release()
    record("F09", dict(owner_lock_exists=path.exists()),
           "A lock instance without ownership must not release another owner's lock", not path.exists())

# Minimal event objects exercise the documented on_bar callback, without fabricating venue events.
from types import SimpleNamespace as NS
def event(seq, open_, high, low, close):
    return NS(seq=seq, bar=NS(symbol="BTCUSDT", open=D(open_), high=D(high), low=D(low), close=D(close)))
s = DcaStrategy(symbol="BTCUSDT", base_order_qty=D("1"), safety_order_qty=D("1"),
                max_safety_orders=2, price_deviation_pct=D("0.1"), take_profit_pct=D("1"))
s.on_bar(event(0, "100", "100", "100", "100"), D("0"))
s.on_bar(event(1, "100", "100", "85", "90"), D("1"))
record("F02", dict(safety_count=s.safety_orders_placed, reference=str(s.last_order_price)),
       "SO intent may be pending; completed level must not advance before fill", s.safety_orders_placed == 1)
s.on_bar(event(2, "100", "100", "95", "100"), D("0.5"))
record("F04", dict(reported_position="0.5", internal_quantity=str(s.total_qty), previous_position=str(s._last_position)),
       "Partial close updates remaining quantity/cost from execution", s.total_qty == D("1"))

print(json.dumps(dict(python=platform.python_version(), scope="OFFLINE_TARGETED_PROBES_NOT_FULL_SUITE",
                     results=results), ensure_ascii=False, indent=2))
