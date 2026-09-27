"""Paper bot runner service (Faz W-B2): drives RUNNING/PAUSED paper bots.

A daemon thread ticks every few seconds. Per bot it fetches the 1m klines
that closed since the last processed bar, advances the bot with
`paper_bot_runner.advance_bot` (the backtest's own bar rule) and persists
runtime, deals and events in one transaction. Nothing here places orders.
"""

import logging
import threading
from dataclasses import dataclass, replace
from typing import Callable

from dcabot.application.futures_grid_runner import advance_futures_grid, prepare_futures_grid_runtime
from dcabot.application.grid_runner import advance_grid, prepare_grid_runtime
from dcabot.application.deal_actions import close_at_market
from dcabot.application.paper_bot_runner import (
    RUNNER_INTERVAL,
    RUNNER_INTERVAL_US,
    BotAdvance,
    ComboPosition,
    advance_bot,
    combo_close_triggered,
)
from dcabot.domain.config import Config
from dcabot.application.portfolio_stats import SNAPSHOT_INTERVAL_US, SNAPSHOT_RETENTION_US, portfolio_equity
from dcabot.application.sector_dca import SectorDcaError, derive_deal_config, max_deal_quote_cost, parse_sector_dca
from dcabot.domain.engine import State
from dcabot.domain.numbers import Q, number
from dcabot.persistence.bot_store import BotPairRuntime, BotRecord, BotRuntime, BotStore, BotStoreError

LOGGER = logging.getLogger(__name__)
MAX_CATCHUP_BARS = 1000
REPLAY_MAX_BARS = 10_080  # 7 days of 1m bars, one synchronous run
REASON_KILL_SWITCH = "KILL_SWITCH_ACTIVE"


def _cooldown_until_us(config: object, deals: list) -> int:
    """Seed the in-memory cooldown from the last close.

    The cooldown is bar-time based, so a restart or a slow tick must not
    skip it -- the seed is recomputed from stored deals on every pass."""

    cooldown = config.get("cooldown_seconds", 0) if isinstance(config, dict) else 0
    if type(cooldown) is not int or cooldown <= 0:
        return 0
    last_close = max((deal.closed_at_us for deal in deals if deal.closed_at_us is not None), default=None)
    if last_close is None:
        return 0
    return last_close + cooldown * 1_000_000
REASON_MARKET_DATA = "MARKET_DATA_UNAVAILABLE"


class ReplayError(Exception):
    """A historical run refused or failed; the API layer maps it to a problem."""

    def __init__(self, code: str, message: str, status: int = 422, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.field = field


@dataclass(frozen=True)
class RunnerDeps:
    store: BotStore
    market: object
    fetch_range: Callable[..., tuple]
    transport_error: type[Exception]
    template_loader: Callable[[], dict]
    clock_us: Callable[[], int]
    kill_switch_engaged: Callable[[], bool]
    record_event: Callable[[str, str, str, int], None] | None = None
    futures_market: object | None = None
    fetch_futures_range: Callable[..., tuple] | None = None
    fetch_funding: Callable[..., tuple] | None = None


_RUNNER_DEAL_LANDMARK = {
    "DEAL_STARTED": "DEAL_OPENED",
    "DEAL_CLOSED": "DEAL_CLOSED",
    "SAFETY_ORDER_FILLED": "SAFETY_ORDER_FILLED",
}


class PaperBotRunner:
    def __init__(self, deps: RunnerDeps, *, interval_seconds: float = 15.0) -> None:
        self.deps = deps
        self.interval_seconds = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # --- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="paper-bot-runner", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop.is_set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception:  # never let one bad tick kill the runner thread
                LOGGER.exception("paper bot runner tick failed")
            self._stop.wait(self.interval_seconds)

    # --- bot start hook -----------------------------------------------------

    def _derive_single_runtime(self, record, params, template, reference_price, last_open, now) -> BotRuntime:
        """One engine config for a single-pair bot; live and replay share it."""

        rules = self.deps.market.symbol_rules(params.symbol)
        raw = derive_deal_config(
            params, rules=rules, reference_price=reference_price, budget=number(record.budget), template=template
        )
        return BotRuntime(record.bot_id, raw, State(), 0, Q(0), last_open, now)

    def _derive_multi_runtimes(self, record, params, template, ref_prices, last_open, now) -> list:
        """One pair runtime per symbol; the budget gate is the live one."""

        cap = max_deal_quote_cost(
            params, fee_rate=number(template["fee_rate"]), fee_quantum=number(template["fee_quantum"])
        )
        if cap * params.max_active_deals > number(record.budget):
            raise SectorDcaError(
                "SECTOR_MULTI_BUDGET_EXCEEDED",
                f"{params.max_active_deals} eşzamanlı deal için bütçe yetersiz.",
                field="budget",
            )
        runtimes = []
        for symbol in params.symbols:
            pair_params = replace(params, symbol=symbol)
            rules = self.deps.market.symbol_rules(symbol)
            raw = derive_deal_config(
                pair_params, rules=rules, reference_price=ref_prices[symbol], budget=cap, template=template
            )
            runtimes.append(BotPairRuntime(record.bot_id, symbol, raw, State(), Q(0), last_open, now))
        return runtimes

    def prepare_start(self, record: BotRecord) -> None:
        """Create the bot's runtime on first start: an engine config derived
        from its sector parameters at current venue rules and price. A later
        restart keeps the existing runtime (an open deal continues)."""

        if record.strategy_type == "GRID":
            if self.deps.store.get_grid_runtime(record.bot_id) is not None:
                return
            rules = self.deps.market.symbol_rules(record.symbol)
            grid_runtime = prepare_grid_runtime(
                record.bot_id, record.strategy, rules, investment=record.budget, now_us=self.deps.clock_us()
            )
            self.deps.store.save_grid_runtime(grid_runtime)
            return
        if record.strategy_type == "FUTURES_GRID":
            if self.deps.store.get_grid_runtime(record.bot_id) is not None:
                return
            if self.deps.futures_market is None:
                raise ValueError("FUTURES_RUNNER_UNAVAILABLE: Futures market bağlı değil.")
            rules = self.deps.futures_market.symbol_rules(record.symbol)
            grid_runtime = prepare_futures_grid_runtime(
                record.bot_id, record.strategy, rules, investment=record.budget, now_us=self.deps.clock_us()
            )
            self.deps.store.save_grid_runtime(grid_runtime)
            return
        if self.deps.store.get_runtime(record.bot_id) is not None:
            return
        params = parse_sector_dca(record.strategy)
        if len(params.symbols) > 1:
            self._prepare_multi_start(record, params)
            return
        now = self.deps.clock_us()
        current_bar_open = now // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US
        runtime = self._derive_single_runtime(
            record, params, self.deps.template_loader(), self.deps.market.last_price(params.symbol), current_bar_open, now
        )
        self.deps.store.save_runtime(runtime)

    def _prepare_multi_start(self, record, params) -> None:
        """One pair runtime per symbol, each reserving a full deal's max cost.

        The budget gate is pure multiplication: `max_active_deals` worst-case
        deals must fit the budget. Each pair runtime is seeded with the
        per-deal cap as its equity, so no pair can ever deploy more than
        one deal's ceiling at any price.
        """

        if self.deps.store.get_pair_runtimes(record.bot_id):
            return
        template = self.deps.template_loader()
        now = self.deps.clock_us()
        current_bar_open = now // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US
        ref = {symbol: self.deps.market.last_price(symbol) for symbol in params.symbols}
        runtimes = self._derive_multi_runtimes(record, params, template, ref, current_bar_open, now)
        self.deps.store.save_pair_step(tuple(runtimes))

    # --- historical run -----------------------------------------------------

    def run_replay(self, bot_id: str, start_us: int, end_us: int) -> dict:
        """Run a fresh STOPPED bot over [start_us, end_us) of closed 1m bars.

        The same bar rule, config derivation and combo evaluation as the
        live runner; runtime, deals and events persist in one guarded
        write, so a market failure or a concurrent start leaves no
        partial state. Afterwards the bot can start and continue live
        from the replay's last bar.
        """

        store = self.deps.store
        bot = store.get(bot_id)
        if bot.mode != "PAPER":
            raise ReplayError(
                "TESTNET_REPLAY_NOT_ENABLED",
                "Geçmiş çalıştırma şimdilik yalnız Paper botlarda yapılabilir.",
                status=409,
            )
        if bot.status != "STOPPED" or bot.archived_at_us is not None:
            raise ReplayError(
                "REPLAY_STATUS_INVALID",
                "Geçmiş çalıştırma yalnız hiç çalışmamış, durdurulmuş bir botla yapılabilir.",
                status=409,
            )
        if (
            store.get_runtime(bot_id) is not None
            or store.get_pair_runtimes(bot_id)
            or store.get_grid_runtime(bot_id) is not None
            or store.list_deals(bot_id)
        ):
            raise ReplayError(
                "REPLAY_STATE_EXISTS",
                "Bu botun zaten çalışmışlığı var; geçmiş çalıştırma bir kez yapılır.",
                status=409,
            )
        now = self.deps.clock_us()
        last_closed = now // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US
        if start_us >= end_us:
            raise ReplayError("REPLAY_RANGE_INVALID", "Bitiş başlangıçtan sonra olmalıdır.", field="end_date")
        if start_us >= last_closed:
            raise ReplayError("REPLAY_NO_BARS", "Seçilen aralıkta kapanmış mum yok.", field="start_date")
        end_us = min(end_us, last_closed)
        if (end_us - start_us) // RUNNER_INTERVAL_US > REPLAY_MAX_BARS:
            raise ReplayError(
                "REPLAY_RANGE_TOO_LONG",
                f"En fazla {REPLAY_MAX_BARS} mum (7 gün); aralığı kısaltın.",
                field="start_date",
            )
        if bot.strategy_type in ("GRID", "FUTURES_GRID"):
            return self._replay_grid(bot, start_us, end_us, now)
        return self._replay_dca(bot, start_us, end_us, now)

    def _replay_fetch(self, fetch, symbol: str, start_us: int, end_us: int, now: int):
        try:
            return fetch(
                symbol,
                interval=RUNNER_INTERVAL,
                start_us=start_us,
                end_us=end_us,
                max_bars=REPLAY_MAX_BARS,
                now_us=now,
                allowed_symbols=frozenset({symbol}),
            )
        except self.deps.transport_error as exc:
            raise ReplayError(getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), str(exc), status=502) from exc

    def _replay_dca(self, bot, start_us: int, end_us: int, now: int) -> dict:
        store = self.deps.store
        params = parse_sector_dca(bot.strategy)
        symbols = list(params.symbols)
        fetched = {
            symbol: self._replay_fetch(self.deps.fetch_range, symbol, start_us, end_us, now) for symbol in symbols
        }
        if not any(fetched.values()):
            raise ReplayError("REPLAY_NO_BARS", "Seçilen aralıkta mum bulunamadı.", field="start_date")
        template = self.deps.template_loader()
        multi = len(symbols) > 1
        firsts = {symbol: min(k.open_time_us for k in bars) for symbol, bars in fetched.items() if bars}
        missing = [symbol for symbol in symbols if symbol not in firsts]
        if missing:
            raise ReplayError(
                "REPLAY_NO_BARS", f"{', '.join(missing)} için aralıkta mum yok.", field="start_date"
            )
        seed_open = min(firsts.values()) - RUNNER_INTERVAL_US
        by_symbol = {symbol: {k.open_time_us: k for k in fetched[symbol]} for symbol in symbols}
        ref = {symbol: number(by_symbol[symbol][firsts[symbol]].close) for symbol in symbols}
        times = sorted({t for per_symbol in by_symbol.values() for t in per_symbol})
        deals: dict[int, object] = {}
        events: list = []
        if multi:
            states = {r.symbol: r for r in self._derive_multi_runtimes(bot, params, template, ref, seed_open, now)}
            advanced = [states[symbol] for symbol in symbols]
            next_seq = 0
            open_count = 0
            for moment in times:
                bar_now = moment + RUNNER_INTERVAL_US
                for symbol in symbols:
                    kline = by_symbol[symbol].get(moment)
                    if kline is None:
                        continue
                    pair = states[symbol]
                    symbol_deals = [deal for deal in deals.values() if deal.symbol == symbol]
                    open_deal = next((deal for deal in reversed(symbol_deals) if deal.closed_at_us is None), None)
                    pseudo = BotRuntime(bot.bot_id, pair.config, pair.state, next_seq, pair.prev_net, pair.last_bar_open_us, bar_now)
                    result = advance_bot(
                        pseudo,
                        (kline,),
                        open_deal=open_deal,
                        allow_new_deal=open_count < params.max_active_deals,
                        now_us=bar_now,
                        cooldown_until_us=_cooldown_until_us(pair.config, tuple(symbol_deals)),
                        symbol=symbol,
                    )
                    next_seq = result.runtime.deal_sequence
                    fresh = BotPairRuntime(
                        bot.bot_id, symbol, pair.config, result.runtime.state,
                        result.runtime.prev_net, result.runtime.last_bar_open_us, bar_now,
                    )
                    states[symbol] = fresh
                    for index, existing in enumerate(advanced):
                        if existing.symbol == symbol:
                            advanced[index] = fresh
                            break
                    for deal in result.deals:
                        if deal.deal_sequence not in deals:
                            open_count += 1
                        deals[deal.deal_sequence] = deal
                        if deal.closed_at_us is not None:
                            open_count -= 1
                    events.extend(result.events)
                if params.combined_take_profit is not None:
                    self._combo_close_multi(params.combined_take_profit, states, advanced, {}, deals, events, bar_now)
                    for existing in advanced:
                        states[existing.symbol] = existing
                    open_count = sum(1 for deal in deals.values() if deal.closed_at_us is None)
            final_states = list(advanced)
            last_open = max(state.last_bar_open_us for state in final_states)
        else:
            symbol = symbols[0]
            runtime = self._derive_single_runtime(bot, params, template, ref[symbol], seed_open, now)
            for moment in times:
                bar_now = moment + RUNNER_INTERVAL_US
                prior = list(deals.values())
                open_deal = next((deal for deal in reversed(prior) if deal.closed_at_us is None), None)
                result = advance_bot(
                    runtime,
                    (by_symbol[symbol][moment],),
                    open_deal=open_deal,
                    allow_new_deal=True,
                    now_us=bar_now,
                    cooldown_until_us=_cooldown_until_us(runtime.config, tuple(prior)),
                    symbol=symbol,
                )
                if params.combined_take_profit is not None:
                    combo = self._combo_close_single(params.combined_take_profit, prior, result, bar_now)
                    if combo is not None:
                        result = combo
                runtime = result.runtime
                for deal in result.deals:
                    deals[deal.deal_sequence] = deal
                events.extend(result.events)
            final_states = [runtime]
            last_open = runtime.last_bar_open_us
        ordered = tuple(deals[key] for key in sorted(deals))
        with store.guarded():
            fresh = store.get(bot.bot_id)
            if fresh.status != "STOPPED" or fresh.archived_at_us is not None:
                raise ReplayError(
                    "REPLAY_STATUS_INVALID",
                    "Çalıştırma sırasında bot durumu değişti; hiçbir şey yazılmadı.",
                    status=409,
                )
            if store.get_runtime(bot.bot_id) is not None or store.get_pair_runtimes(bot.bot_id) or store.list_deals(bot.bot_id):
                raise ReplayError(
                    "REPLAY_STATE_EXISTS",
                    "Çalıştırma sırasında bot çalışmış; hiçbir şey yazılmadı.",
                    status=409,
                )
            if multi:
                store.save_pair_step(tuple(final_states), deals=ordered, events=tuple(events))
            else:
                store.save_runtime(final_states[0], deals=ordered, events=tuple(events))
        symbols_by_seq = {deal.deal_sequence: deal.symbol for deal in ordered} if multi else None
        self._emit_deal_events(bot, events, symbols_by_seq)
        return {
            "bars": len(times),
            "deals_opened": sum(1 for event in events if event.kind == "DEAL_STARTED"),
            "deals_closed": sum(1 for event in events if event.kind == "DEAL_CLOSED"),
            "fills": 0,
            "events": len(events),
            "first_bar_open_us": min(times),
            "last_bar_open_us": last_open,
            "symbols": symbols,
            "stopped": None,
        }

    def _replay_grid(self, bot, start_us: int, end_us: int, now: int) -> dict:
        store = self.deps.store
        futures = bot.strategy_type == "FUTURES_GRID"
        if futures and (self.deps.fetch_futures_range is None or self.deps.fetch_funding is None):
            raise ReplayError("FUTURES_REPLAY_UNAVAILABLE", "Futures verisi bağlı değil.", status=409)
        fetch = self.deps.fetch_futures_range if futures else self.deps.fetch_range
        klines = self._replay_fetch(fetch, bot.symbol, start_us, end_us, now)
        if not klines:
            raise ReplayError("REPLAY_NO_BARS", "Seçilen aralıkta mum bulunamadı.", field="start_date")
        if futures:
            try:
                funding = self.deps.fetch_funding(
                    bot.symbol, start_us=start_us, end_us=end_us, allowed_symbols=frozenset({bot.symbol})
                )
            except self.deps.transport_error as exc:
                raise ReplayError(getattr(exc, "code", "PUBLIC_UPSTREAM_UNAVAILABLE"), str(exc), status=502) from exc
        else:
            funding = ()
        market = self.deps.futures_market if futures else self.deps.market
        rules = market.symbol_rules(bot.symbol)
        prepare = prepare_futures_grid_runtime if futures else prepare_grid_runtime
        runtime = prepare(bot.bot_id, bot.strategy, rules, investment=bot.budget, now_us=now)
        seed_open = min(k.open_time_us for k in klines) - RUNNER_INTERVAL_US
        runtime = replace(runtime, last_bar_open_us=seed_open)
        if futures:
            result = advance_futures_grid(runtime, klines, funding, now_us=end_us)
        else:
            result = advance_grid(runtime, klines, now_us=end_us)
        with store.guarded():
            fresh = store.get(bot.bot_id)
            if fresh.status != "STOPPED" or fresh.archived_at_us is not None:
                raise ReplayError(
                    "REPLAY_STATUS_INVALID",
                    "Çalıştırma sırasında bot durumu değişti; hiçbir şey yazılmadı.",
                    status=409,
                )
            if store.get_grid_runtime(bot.bot_id) is not None or store.list_deals(bot.bot_id):
                raise ReplayError(
                    "REPLAY_STATE_EXISTS",
                    "Çalıştırma sırasında bot çalışmış; hiçbir şey yazılmadı.",
                    status=409,
                )
            store.save_grid_runtime(result.runtime, events=result.events)
            store.prune_bot_events(bot.bot_id)
        self._emit_grid_events(bot, result.events)
        return {
            "bars": sum(1 for k in klines if k.open_time_us <= result.runtime.last_bar_open_us),
            "deals_opened": 0,
            "deals_closed": 0,
            "fills": sum(1 for event in result.events if event.kind == "GRID_FILL"),
            "events": len(result.events),
            "first_bar_open_us": seed_open + RUNNER_INTERVAL_US,
            "last_bar_open_us": result.runtime.last_bar_open_us,
            "symbols": [bot.symbol],
            "stopped": result.stopped_reason,
        }

    # --- one pass -----------------------------------------------------------

    def tick(self) -> None:
        now = self.deps.clock_us()
        bots = [
            bot for bot in self.deps.store.list()
            if bot.mode == "PAPER" and bot.status in ("RUNNING", "PAUSED")
        ]
        if self.deps.kill_switch_engaged():
            for bot in bots:
                self._note_runner_status(bot, bot.status, REASON_KILL_SWITCH, now)
            self._maybe_snapshot(now)
            return
        for bot in bots:
            self._advance(bot, now)
        self._maybe_snapshot(now)

    def _note_runner_status(self, bot: BotRecord, status: str, reason: str | None, now: int):
        """Runner-side status write; a landmark only when it changes."""
        after = self.deps.store.set_runner_status(bot.bot_id, status, reason, now_us=now)
        if after.revision != bot.revision and self.deps.record_event is not None:
            note = f" ({reason})" if reason else ""
            self.deps.record_event("BOT_STATUS", bot.bot_id, f"Bot durumu: {status}{note}.", now)
        return after

    def _emit_deal_events(self, bot: BotRecord, events, symbols: dict | None = None) -> None:
        """Landmarks for runner-driven deal milestones (open/close/SO fill)."""
        if self.deps.record_event is None:
            return
        for event in events:
            kind = _RUNNER_DEAL_LANDMARK.get(event.kind)
            if kind is None:
                continue
            seq = event.detail.get("deal")
            ref = f"{bot.bot_id}:{seq}"
            tag = ""
            if symbols is not None and seq in symbols:
                tag = f" ({symbols[seq]})"
            if event.kind == "DEAL_STARTED":
                summary = f"Deal {seq} açıldı{tag}."
            elif event.kind == "DEAL_CLOSED":
                summary = f"Deal {seq} kapandı{tag} ({event.detail.get('reason')})."
            else:
                summary = f"SO doldu (deal {seq}, #{event.detail.get('index')}){tag}."
            self.deps.record_event(kind, ref, summary, event.time_us)

    def _emit_grid_events(self, bot: BotRecord, events) -> None:
        """Landmark for grid terminal stops only; fills stay in bot events."""
        if self.deps.record_event is None:
            return
        for event in events:
            if event.kind in ("GRID_STOP_LOSS", "GRID_LIQ_ESTIMATE_HIT"):
                why = "stop-loss" if event.kind == "GRID_STOP_LOSS" else "likidasyon tahmini"
                self.deps.record_event("GRID_STOPPED", bot.bot_id, f"Grid {why} ile durdu.", event.time_us)
            elif event.kind == "GRID_TAKE_PROFIT":
                self.deps.record_event("GRID_STOPPED", bot.bot_id, "Grid take-profit ile durdu.", event.time_us)

    def _advance_grid(self, bot: BotRecord, now: int) -> None:
        store = self.deps.store
        runtime = store.get_grid_runtime(bot.bot_id)
        if runtime is None:
            self._note_runner_status(bot, "ERROR", "RUNTIME_MISSING", now)
            return
        start_us = runtime.last_bar_open_us + RUNNER_INTERVAL_US
        end_us = min(now // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US, start_us + MAX_CATCHUP_BARS * RUNNER_INTERVAL_US)
        if start_us >= end_us:
            return
        futures = bot.strategy_type == "FUTURES_GRID"
        if futures and (self.deps.fetch_futures_range is None or self.deps.fetch_funding is None):
            self._note_runner_status(bot, "ERROR", "FUTURES_RUNNER_UNAVAILABLE", now)
            return
        fetch = self.deps.fetch_futures_range if futures else self.deps.fetch_range
        try:
            klines = fetch(
                bot.symbol,
                interval=RUNNER_INTERVAL,
                start_us=start_us,
                end_us=end_us,
                max_bars=MAX_CATCHUP_BARS,
                now_us=now,
                allowed_symbols=frozenset({bot.symbol}),
            )
            funding = (
                ()
                if not futures
                else self.deps.fetch_funding(
                    bot.symbol,
                    start_us=start_us,
                    end_us=end_us,
                    allowed_symbols=frozenset({bot.symbol}),
                )
            )
        except self.deps.transport_error:
            self._note_runner_status(bot, bot.status, REASON_MARKET_DATA, now)
            return
        with store.guarded():
            runtime = store.get_grid_runtime(bot.bot_id)
            if runtime is None:
                self._note_runner_status(bot, "ERROR", "RUNTIME_MISSING", now)
                return
            try:
                if futures:
                    result = advance_futures_grid(runtime, klines, funding, now_us=now)
                else:
                    result = advance_grid(runtime, klines, now_us=now)
                store.save_grid_runtime(result.runtime, events=result.events)
                store.prune_bot_events(bot.bot_id)
                self._emit_grid_events(bot, result.events)
            except (ValueError, BotStoreError) as exc:
                LOGGER.warning("paper grid bot %s stopped with an error: %s", bot.bot_id, exc)
                self._note_runner_status(bot, "ERROR", f"RUNNER_ERROR: {str(exc)[:160]}", now)
                return
            if result.stopped_reason is not None:
                self._note_runner_status(bot, "STOPPED", result.stopped_reason, now)
                return
        if bot.status_reason is not None:
            self._note_runner_status(bot, bot.status, None, now)

    def _maybe_snapshot(self, now: int) -> None:
        """Hourly portfolio point plus 90-day prune. Snapshots are
        auxiliary: a failure is logged and never breaks the tick."""

        store = self.deps.store
        try:
            with store.guarded():
                last = store.latest_portfolio_snapshot_time()
                if last is not None and now - last < SNAPSHOT_INTERVAL_US:
                    return
                records = store.list()
                deals = {record.bot_id: store.list_deals(record.bot_id) for record in records}
                runtimes = {}
                for record in records:
                    runtime = store.get_runtime(record.bot_id)
                    if runtime is not None:
                        runtimes[record.bot_id] = runtime
                point = portfolio_equity(records, deals, runtimes)
                store.save_portfolio_snapshot(now, point["equity"], point["realized"], point["unrealized"])
                store.prune_portfolio_snapshots(before_us=now - SNAPSHOT_RETENTION_US)
        except (ValueError, BotStoreError) as exc:
            LOGGER.warning("portfolio snapshot skipped: %s", exc)

    def _combo_close_single(self, target, prior, advance, now):
        """Close the open deal when the combined target hits (single-pair).

        The post-step book overlays pre-step deals with touched rows:
        advance only returns touched rows, so an untouched open deal
        is invisible in `advance.deals`. The engine holds at most one
        open deal; anything else fails closed (no blind close).
        """

        runtime = advance.runtime
        post = {deal.deal_sequence: deal for deal in prior}
        post.update({deal.deal_sequence: deal for deal in advance.deals})
        open_deals = [deal for deal in post.values() if deal.closed_at_us is None]
        if len(open_deals) != 1 or runtime.state.mark is None:
            return None
        position = runtime.state.position
        if not position.qty:
            return None
        combo = ComboPosition(
            position.qty, position.cost, runtime.state.mark, runtime.config.get("direction", "LONG")
        )
        if not combo_close_triggered((combo,), target):
            return None
        config = Config.parse(runtime.config)
        out = close_at_market(
            config, runtime.state, open_deals[0], runtime.prev_net,
            price=runtime.state.mark, now_us=now, reason="TAKE_PROFIT",
        )
        new_runtime = replace(runtime, state=out.state, prev_net=out.prev_net)
        post[out.deal.deal_sequence] = out.deal
        new_deals = tuple(post[key] for key in sorted(post))
        return BotAdvance(new_runtime, new_deals, advance.events + (out.event,))

    def _combo_close_multi(self, target, runtimes, advanced, deals, touched, events, now) -> None:
        """Close every open pair deal when the combined target hits.

        States overlay stored runtimes with this step's advances, so a
        pair that had no new bars still counts at its current mark. Any
        missing mark or state fails the whole evaluation closed.
        """

        post = dict(deals)
        post.update(touched)
        open_deals = [deal for deal in post.values() if deal.closed_at_us is None]
        if not open_deals:
            return
        fresh = {runtime.symbol: runtime for runtime in advanced}
        positions = []
        closable = []
        for deal in open_deals:
            runtime = fresh.get(deal.symbol or "") or runtimes.get(deal.symbol or "")
            if runtime is None or runtime.state.mark is None:
                return
            position = runtime.state.position
            if not position.qty:
                return
            positions.append(
                ComboPosition(
                    position.qty, position.cost, runtime.state.mark, runtime.config.get("direction", "LONG")
                )
            )
            closable.append((deal, runtime))
        if not combo_close_triggered(tuple(positions), target):
            return
        for deal, runtime in closable:
            config = Config.parse(runtime.config)
            out = close_at_market(
                config, runtime.state, deal, runtime.prev_net,
                price=runtime.state.mark, now_us=now, reason="TAKE_PROFIT",
            )
            replacement = BotPairRuntime(
                runtime.bot_id, runtime.symbol, runtime.config, out.state, out.prev_net,
                runtime.last_bar_open_us, now,
            )
            for index, existing in enumerate(advanced):
                if existing.symbol == runtime.symbol:
                    advanced[index] = replacement
                    break
            else:
                advanced.append(replacement)
            touched[deal.deal_sequence] = out.deal
            events.append(out.event)

    def _advance(self, bot: BotRecord, now: int) -> None:
        if bot.strategy_type in ("GRID", "FUTURES_GRID"):
            self._advance_grid(bot, now)
            return
        store = self.deps.store
        if store.get_pair_runtimes(bot.bot_id):
            self._advance_multi(bot, now)
            return
        params = parse_sector_dca(bot.strategy)
        # Range probe outside the guard; the venue fetch must never hold it.
        # The guarded step re-reads fresh runtime underneath.
        runtime = store.get_runtime(bot.bot_id)
        if runtime is None:
            self._note_runner_status(bot, "ERROR", "RUNTIME_MISSING", now)
            return
        start_us = runtime.last_bar_open_us + RUNNER_INTERVAL_US
        end_us = min(now // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US, start_us + MAX_CATCHUP_BARS * RUNNER_INTERVAL_US)
        if start_us >= end_us:
            return
        try:
            klines = self.deps.fetch_range(
                bot.symbol,
                interval=RUNNER_INTERVAL,
                start_us=start_us,
                end_us=end_us,
                max_bars=MAX_CATCHUP_BARS,
                now_us=now,
                allowed_symbols=frozenset({bot.symbol}),
            )
        except self.deps.transport_error:
            self._note_runner_status(bot, bot.status, REASON_MARKET_DATA, now)
            return
        # Read-compute-write under one guard: a deal action on the API
        # side takes the same guard, so neither step can silently lose the
        # other's runtime write. Stale klines are harmless -- advance_bot
        # skips every bar at or below the fresh last_bar_open_us.
        with store.guarded():
            runtime = store.get_runtime(bot.bot_id)
            if runtime is None:
                self._note_runner_status(bot, "ERROR", "RUNTIME_MISSING", now)
                return
            deals = store.list_deals(bot.bot_id)
            open_deal = next((deal for deal in reversed(deals) if deal.closed_at_us is None), None)
            try:
                result = advance_bot(
                    runtime,
                    klines,
                    open_deal=open_deal,
                    allow_new_deal=bot.status == "RUNNING",
                    now_us=now,
                    cooldown_until_us=_cooldown_until_us(runtime.config, deals),
                    symbol=bot.symbol,
                )
                if params.combined_take_profit is not None:
                    combo = self._combo_close_single(params.combined_take_profit, deals, result, now)
                    if combo is not None:
                        result = combo
                store.save_runtime(result.runtime, deals=result.deals, events=result.events)
                self._emit_deal_events(bot, result.events)
            except (ValueError, BotStoreError) as exc:
                LOGGER.warning("paper bot %s stopped with an error: %s", bot.bot_id, exc)
                self._note_runner_status(bot, "ERROR", f"RUNNER_ERROR: {str(exc)[:160]}", now)
                return
        if bot.status_reason is not None:
            self._note_runner_status(bot, bot.status, None, now)

    def _advance_multi(self, bot: BotRecord, now: int) -> None:
        store = self.deps.store
        params = parse_sector_dca(bot.strategy)
        runtimes = {runtime.symbol: runtime for runtime in store.get_pair_runtimes(bot.bot_id)}
        if set(runtimes) != set(params.symbols):
            self._note_runner_status(bot, "ERROR", "RUNTIME_MISMATCH", now)
            return
        # Venue fetches outside the guard, one symbol at a time.
        fetched: dict[str, tuple] = {}
        for symbol in params.symbols:
            start_us = runtimes[symbol].last_bar_open_us + RUNNER_INTERVAL_US
            end_us = min(now // RUNNER_INTERVAL_US * RUNNER_INTERVAL_US, start_us + MAX_CATCHUP_BARS * RUNNER_INTERVAL_US)
            if start_us >= end_us:
                continue
            try:
                fetched[symbol] = self.deps.fetch_range(
                    symbol,
                    interval=RUNNER_INTERVAL,
                    start_us=start_us,
                    end_us=end_us,
                    max_bars=MAX_CATCHUP_BARS,
                    now_us=now,
                    allowed_symbols=frozenset({symbol}),
                )
            except self.deps.transport_error:
                self._note_runner_status(bot, bot.status, REASON_MARKET_DATA, now)
                return
        if not fetched:
            return
        with store.guarded():
            runtimes = {runtime.symbol: runtime for runtime in store.get_pair_runtimes(bot.bot_id)}
            if set(runtimes) != set(params.symbols):
                self._note_runner_status(bot, "ERROR", "RUNTIME_MISMATCH", now)
                return
            deals = {deal.deal_sequence: deal for deal in store.list_deals(bot.bot_id)}
            next_seq = max(deals, default=0)
            open_count = sum(1 for deal in deals.values() if deal.closed_at_us is None)
            advanced: list[BotPairRuntime] = []
            touched: dict[int, object] = {}
            events: list = []
            try:
                for symbol in params.symbols:
                    if symbol not in fetched:
                        continue
                    pair = runtimes[symbol]
                    symbol_deals = [deal for deal in list(deals.values()) + list(touched.values()) if deal.symbol == symbol]
                    open_deal = next((deal for deal in reversed(symbol_deals) if deal.closed_at_us is None), None)
                    pseudo = BotRuntime(bot.bot_id, pair.config, pair.state, next_seq, pair.prev_net, pair.last_bar_open_us, now)
                    result = advance_bot(
                        pseudo,
                        fetched[symbol],
                        open_deal=open_deal,
                        allow_new_deal=bot.status == "RUNNING" and open_count < params.max_active_deals,
                        now_us=now,
                        cooldown_until_us=_cooldown_until_us(pair.config, tuple(symbol_deals)),
                        symbol=symbol,
                    )
                    next_seq = result.runtime.deal_sequence
                    advanced.append(
                        BotPairRuntime(
                            bot.bot_id, symbol, pair.config, result.runtime.state,
                            result.runtime.prev_net, result.runtime.last_bar_open_us, now,
                        )
                    )
                    for deal in result.deals:
                        if deal.deal_sequence not in deals and deal.deal_sequence not in touched:
                            open_count += 1
                        touched[deal.deal_sequence] = deal
                        if deal.closed_at_us is not None:
                            open_count -= 1
                    events.extend(result.events)
                if params.combined_take_profit is not None:
                    self._combo_close_multi(
                        params.combined_take_profit, runtimes, advanced, deals, touched, events, now
                    )
                store.save_pair_step(
                    tuple(advanced), deals=tuple(touched[key] for key in sorted(touched)), events=tuple(events)
                )
                self._emit_deal_events(bot, events, {deal.deal_sequence: deal.symbol for deal in touched.values()})
            except (ValueError, BotStoreError) as exc:
                LOGGER.warning("paper bot %s stopped with an error: %s", bot.bot_id, exc)
                self._note_runner_status(bot, "ERROR", f"RUNNER_ERROR: {str(exc)[:160]}", now)
                return
        if bot.status_reason is not None:
            self._note_runner_status(bot, bot.status, None, now)
