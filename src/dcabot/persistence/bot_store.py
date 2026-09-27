"""Durable bot records (Faz W-B1): one SQLite file, one row per bot.

A bot is a user-facing definition (name, mode, sector strategy parameters,
budget) plus a lifecycle status. It holds no market state and no order
authority; the runner (W-B2) reads RUNNING bots and drives deals. Every
write bumps `revision` so concurrent edits are detected, never merged.
"""

import contextlib
import functools
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from dcabot.domain.engine import State
from dcabot.domain.numbers import Q, ratio

BOT_MODES = ("PAPER", "TESTNET")
BOT_STATUSES = ("STOPPED", "RUNNING", "PAUSED", "ERROR")
BOT_ACTIONS = ("start", "pause", "resume", "stop")
_TRANSITIONS = {
    ("STOPPED", "start"): "RUNNING",
    ("RUNNING", "pause"): "PAUSED",
    ("PAUSED", "resume"): "RUNNING",
    ("RUNNING", "stop"): "STOPPED",
    ("PAUSED", "stop"): "STOPPED",
    ("ERROR", "stop"): "STOPPED",
}


class BotStoreError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class BotRecord:
    bot_id: str
    name: str
    strategy_type: str
    mode: str
    symbol: str
    strategy: dict
    budget: str
    status: str
    status_reason: str | None
    revision: int
    created_at_us: int
    updated_at_us: int
    archived_at_us: int | None


def next_status(current: str, action: str) -> str:
    """Pure lifecycle rule; an illegal pair fails closed instead of no-op."""

    target = _TRANSITIONS.get((current, action))
    if target is None:
        raise BotStoreError("BOT_TRANSITION_INVALID", f"{current} durumundaki bot için '{action}' geçersiz.")
    return target


def _validate_id(bot_id: str) -> None:
    if (
        not isinstance(bot_id, str)
        or not 1 <= len(bot_id) <= 64
        or not all(ch.isascii() and (ch.isalnum() or ch in "_-") for ch in bot_id)
    ):
        raise BotStoreError("BOT_ID_INVALID", "Bot kimliği geçersiz.")


def _locked(method):
    """Serialize every use of the shared SQLite connection: the API threads
    and the bot runner thread share one store."""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper


@dataclass(frozen=True, slots=True)
class BotRuntime:
    """Runner-owned progress of one bot: the engine config it trades with,
    the engine state between bars, and the last closed bar it processed."""

    bot_id: str
    config: dict
    state: State
    deal_sequence: int
    prev_net: Q
    last_bar_open_us: int
    updated_at_us: int


@dataclass(frozen=True, slots=True)
class BotPairRuntime:
    """Runner-owned progress of one pair of a multi-pair DCA bot.

    The deal sequence is shared across pairs and derived from the deals
    table, so it lives here only as a transient advance input, never
    persisted: each pair row keeps its own engine state and bar cursor.
    """

    bot_id: str
    symbol: str
    config: dict
    state: State
    prev_net: Q
    last_bar_open_us: int
    updated_at_us: int


@dataclass(frozen=True, slots=True)
class GridRuntime:
    """Runner-owned progress of one grid bot: the engine snapshot between
    bars plus the last closed bar it processed. The tradable config lives
    in the bot record's strategy; venue quantization is pinned here."""

    bot_id: str
    config: dict
    snapshot: dict
    last_bar_open_us: int
    updated_at_us: int


@dataclass(frozen=True, slots=True)
class BotDeal:
    bot_id: str
    deal_sequence: int
    started_at_us: int
    closed_at_us: int | None
    safety_orders_filled: int
    profit: str | None
    close_reason: str | None
    manual_orders_filled: int = 0
    symbol: str = ""


@dataclass(frozen=True, slots=True)
class BotEvent:
    bot_id: str
    time_us: int
    kind: str
    detail: dict


class BotStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = sqlite3.connect(str(path), isolation_level=None, timeout=5, check_same_thread=False)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS bots (
                    bot_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    strategy_type TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    strategy_json TEXT NOT NULL,
                    budget TEXT NOT NULL,
                    status TEXT NOT NULL,
                    status_reason TEXT,
                    revision INTEGER NOT NULL,
                    created_at_us INTEGER NOT NULL,
                    updated_at_us INTEGER NOT NULL,
                    archived_at_us INTEGER
                )
                """
            )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_runtime (
                    bot_id TEXT PRIMARY KEY REFERENCES bots(bot_id),
                    config_json TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    deal_sequence INTEGER NOT NULL,
                    prev_net TEXT NOT NULL,
                    last_bar_open_us INTEGER NOT NULL,
                    updated_at_us INTEGER NOT NULL
                )
                """
            )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS grid_runtime (
                    bot_id TEXT PRIMARY KEY REFERENCES bots(bot_id),
                    config_json TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    last_bar_open_us INTEGER NOT NULL,
                    updated_at_us INTEGER NOT NULL
                )
                """
            )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_pair_runtime (
                    bot_id TEXT NOT NULL REFERENCES bots(bot_id),
                    symbol TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    prev_net TEXT NOT NULL,
                    last_bar_open_us INTEGER NOT NULL,
                    updated_at_us INTEGER NOT NULL,
                    PRIMARY KEY (bot_id, symbol)
                )
                """
            )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_deals (
                    bot_id TEXT NOT NULL REFERENCES bots(bot_id),
                    deal_sequence INTEGER NOT NULL,
                    started_at_us INTEGER NOT NULL,
                    closed_at_us INTEGER,
                    safety_orders_filled INTEGER NOT NULL,
                    profit TEXT,
                    close_reason TEXT,
                    manual_orders_filled INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (bot_id, deal_sequence)
                )
                """
            )
            deal_columns = {row[1] for row in self.db.execute("PRAGMA table_info(bot_deals)").fetchall()}
            if "manual_orders_filled" not in deal_columns:
                self.db.execute("ALTER TABLE bot_deals ADD COLUMN manual_orders_filled INTEGER NOT NULL DEFAULT 0")
            if "symbol" not in deal_columns:
                self.db.execute("ALTER TABLE bot_deals ADD COLUMN symbol TEXT NOT NULL DEFAULT ''")
                self.db.execute(
                    "UPDATE bot_deals SET symbol = "
                    "(SELECT symbol FROM bots WHERE bots.bot_id = bot_deals.bot_id) "
                    "WHERE symbol = ''"
                )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL REFERENCES bots(bot_id),
                    time_us INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    detail_json TEXT NOT NULL
                )
                """
            )
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    time_us INTEGER PRIMARY KEY,
                    equity TEXT NOT NULL,
                    realized TEXT NOT NULL,
                    unrealized TEXT NOT NULL
                )
                """
            )
        except sqlite3.Error as exc:
            raise BotStoreError("BOT_STORE_UNAVAILABLE", "Bot deposu açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    @_locked
    def create(self, record: BotRecord) -> BotRecord:
        _validate_id(record.bot_id)
        if record.mode not in BOT_MODES or record.status != "STOPPED" or record.revision != 1:
            raise BotStoreError("BOT_RECORD_INVALID", "Yeni bot STOPPED ve revision 1 olmalıdır.")
        try:
            self.db.execute(
                "INSERT INTO bots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    record.bot_id,
                    record.name,
                    record.strategy_type,
                    record.mode,
                    record.symbol,
                    json.dumps(record.strategy, sort_keys=True, separators=(",", ":")),
                    record.budget,
                    record.status,
                    record.status_reason,
                    record.revision,
                    record.created_at_us,
                    record.updated_at_us,
                    record.archived_at_us,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise BotStoreError("BOT_ID_CONFLICT", "Bu kimlikle bir bot zaten var.") from exc
        return record

    @_locked
    def get(self, bot_id: str) -> BotRecord:
        _validate_id(bot_id)
        row = self.db.execute("SELECT * FROM bots WHERE bot_id = ?", (bot_id,)).fetchone()
        if row is None:
            raise BotStoreError("BOT_NOT_FOUND", "Bot bulunamadı.")
        return _record(row)

    @_locked
    def list(self, *, include_archived: bool = False) -> tuple[BotRecord, ...]:
        query = "SELECT * FROM bots"
        if not include_archived:
            query += " WHERE archived_at_us IS NULL"
        query += " ORDER BY created_at_us, bot_id"
        return tuple(_record(row) for row in self.db.execute(query).fetchall())

    @_locked
    def apply_action(self, bot_id: str, action: str, *, expected_revision: int, now_us: int) -> BotRecord:
        current = self.get(bot_id)
        if current.archived_at_us is not None:
            raise BotStoreError("BOT_ARCHIVED", "Arşivlenmiş bot değiştirilemez.")
        if action not in BOT_ACTIONS:
            raise BotStoreError("BOT_TRANSITION_INVALID", "Bilinmeyen işlem.")
        status = next_status(current.status, action)
        return self._update(current, expected_revision, now_us, status=status, status_reason=None)

    @_locked
    def archive(self, bot_id: str, *, expected_revision: int, now_us: int) -> BotRecord:
        current = self.get(bot_id)
        if current.archived_at_us is not None:
            raise BotStoreError("BOT_ARCHIVED", "Bot zaten arşivlenmiş.")
        if current.status != "STOPPED":
            raise BotStoreError("BOT_TRANSITION_INVALID", "Yalnız durdurulmuş bot arşivlenebilir.")
        return self._update(current, expected_revision, now_us, archived_at_us=now_us)

    @_locked
    def _update(self, current: BotRecord, expected_revision: int, now_us: int, **changes) -> BotRecord:
        if current.revision != expected_revision:
            raise BotStoreError("BOT_REVISION_CONFLICT", "Bot başka bir yerde değişti; sayfayı yenileyin.")
        status = changes.get("status", current.status)
        status_reason = changes.get("status_reason", current.status_reason)
        archived = changes.get("archived_at_us", current.archived_at_us)
        cursor = self.db.execute(
            """
            UPDATE bots SET status = ?, status_reason = ?, archived_at_us = ?,
                revision = revision + 1, updated_at_us = ?
            WHERE bot_id = ? AND revision = ?
            """,
            (status, status_reason, archived, now_us, current.bot_id, expected_revision),
        )
        if cursor.rowcount != 1:
            raise BotStoreError("BOT_REVISION_CONFLICT", "Bot başka bir yerde değişti; sayfayı yenileyin.")
        return self.get(current.bot_id)


    # --- runner-owned state -------------------------------------------------

    def get_runtime(self, bot_id: str) -> BotRuntime | None:
        from dcabot.persistence.spot_binding_store import _decode_state, _fraction

        _validate_id(bot_id)
        with self._lock:
            row = self.db.execute(
                "SELECT config_json, state_json, deal_sequence, prev_net, last_bar_open_us, updated_at_us "
                "FROM bot_runtime WHERE bot_id = ?",
                (bot_id,),
            ).fetchone()
        if row is None:
            return None
        try:
            return BotRuntime(
                bot_id=bot_id,
                config=json.loads(row[0]),
                state=_decode_state(json.loads(row[1])),
                deal_sequence=row[2],
                prev_net=_fraction(json.loads(row[3])),
                last_bar_open_us=row[4],
                updated_at_us=row[5],
            )
        except (ValueError, json.JSONDecodeError) as exc:
            raise BotStoreError("BOT_RUNTIME_CORRUPT", "Bot çalışma durumu okunamadı.") from exc

    def save_runtime(
        self,
        runtime: BotRuntime,
        *,
        deals: tuple[BotDeal, ...] = (),
        events: tuple[BotEvent, ...] = (),
    ) -> None:
        """Persist one runner step atomically: state, touched deals, events."""
        from dcabot.persistence.spot_binding_store import _state_payload

        _validate_id(runtime.bot_id)
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.execute(
                    "INSERT OR REPLACE INTO bot_runtime VALUES (?,?,?,?,?,?,?)",
                    (
                        runtime.bot_id,
                        json.dumps(runtime.config, sort_keys=True, separators=(",", ":")),
                        json.dumps(_state_payload(runtime.state), sort_keys=True, separators=(",", ":")),
                        runtime.deal_sequence,
                        json.dumps(ratio(runtime.prev_net)),
                        runtime.last_bar_open_us,
                        runtime.updated_at_us,
                    ),
                )
                for deal in deals:
                    if not deal.symbol:
                        raise BotStoreError("BOT_DEAL_SYMBOL_INVALID", "Deal sembolü boş olamaz.")
                    self.db.execute(
                        "INSERT OR REPLACE INTO bot_deals VALUES (?,?,?,?,?,?,?,?,?)",
                        (
                            deal.bot_id,
                            deal.deal_sequence,
                            deal.started_at_us,
                            deal.closed_at_us,
                            deal.safety_orders_filled,
                            deal.profit,
                            deal.close_reason,
                            deal.manual_orders_filled,
                            deal.symbol,
                        ),
                    )
                for event in events:
                    self.db.execute(
                        "INSERT INTO bot_events (bot_id, time_us, kind, detail_json) VALUES (?,?,?,?)",
                        (event.bot_id, event.time_us, event.kind, json.dumps(event.detail, sort_keys=True)),
                    )
                self.db.execute("COMMIT")
            except sqlite3.Error as exc:
                self.db.execute("ROLLBACK")
                raise BotStoreError("BOT_RUNTIME_WRITE_FAILED", "Bot çalışma durumu yazılamadı.") from exc

    def get_pair_runtimes(self, bot_id: str) -> tuple[BotPairRuntime, ...]:
        from dcabot.persistence.spot_binding_store import _decode_state, _fraction

        _validate_id(bot_id)
        with self._lock:
            rows = self.db.execute(
                "SELECT symbol, config_json, state_json, prev_net, last_bar_open_us, updated_at_us "
                "FROM bot_pair_runtime WHERE bot_id = ? ORDER BY symbol",
                (bot_id,),
            ).fetchall()
        try:
            return tuple(
                BotPairRuntime(
                    bot_id=bot_id,
                    symbol=row[0],
                    config=json.loads(row[1]),
                    state=_decode_state(json.loads(row[2])),
                    prev_net=_fraction(json.loads(row[3])),
                    last_bar_open_us=row[4],
                    updated_at_us=row[5],
                )
                for row in rows
            )
        except (ValueError, json.JSONDecodeError) as exc:
            raise BotStoreError("BOT_RUNTIME_CORRUPT", "Parite çalışma durumu okunamadı.") from exc

    def save_pair_step(
        self,
        runtimes: tuple[BotPairRuntime, ...],
        *,
        deals: tuple[BotDeal, ...] = (),
        events: tuple[BotEvent, ...] = (),
    ) -> None:
        """Persist one multi-pair runner step atomically: pair states, deals, events."""

        from dcabot.persistence.spot_binding_store import _state_payload

        if not runtimes:
            raise BotStoreError("BOT_PAIR_RUNTIME_INVALID", "En az bir parite durumu gerekir.")
        bot_id = runtimes[0].bot_id
        for runtime in runtimes:
            _validate_id(runtime.bot_id)
            if runtime.bot_id != bot_id or not runtime.symbol:
                raise BotStoreError("BOT_PAIR_RUNTIME_INVALID", "Parite durumu aynı bota ait olmalıdır.")
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                for runtime in runtimes:
                    self.db.execute(
                        "INSERT OR REPLACE INTO bot_pair_runtime VALUES (?,?,?,?,?,?,?)",
                        (
                            runtime.bot_id,
                            runtime.symbol,
                            json.dumps(runtime.config, sort_keys=True, separators=(",", ":")),
                            json.dumps(_state_payload(runtime.state), sort_keys=True, separators=(",", ":")),
                            json.dumps(ratio(runtime.prev_net)),
                            runtime.last_bar_open_us,
                            runtime.updated_at_us,
                        ),
                    )
                for deal in deals:
                    if not deal.symbol:
                        raise BotStoreError("BOT_DEAL_SYMBOL_INVALID", "Deal sembolü boş olamaz.")
                    self.db.execute(
                        "INSERT OR REPLACE INTO bot_deals VALUES (?,?,?,?,?,?,?,?,?)",
                        (
                            deal.bot_id,
                            deal.deal_sequence,
                            deal.started_at_us,
                            deal.closed_at_us,
                            deal.safety_orders_filled,
                            deal.profit,
                            deal.close_reason,
                            deal.manual_orders_filled,
                            deal.symbol,
                        ),
                    )
                for event in events:
                    self.db.execute(
                        "INSERT INTO bot_events (bot_id, time_us, kind, detail_json) VALUES (?,?,?,?)",
                        (event.bot_id, event.time_us, event.kind, json.dumps(event.detail, sort_keys=True)),
                    )
                self.db.execute("COMMIT")
            except sqlite3.Error as exc:
                self.db.execute("ROLLBACK")
                raise BotStoreError("BOT_RUNTIME_WRITE_FAILED", "Parite çalışma durumu yazılamadı.") from exc

    def get_grid_runtime(self, bot_id: str) -> GridRuntime | None:
        _validate_id(bot_id)
        with self._lock:
            row = self.db.execute(
                "SELECT config_json, state_json, last_bar_open_us, updated_at_us "
                "FROM grid_runtime WHERE bot_id = ?",
                (bot_id,),
            ).fetchone()
        if row is None:
            return None
        try:
            return GridRuntime(
                bot_id=bot_id,
                config=json.loads(row[0]),
                snapshot=json.loads(row[1]),
                last_bar_open_us=row[2],
                updated_at_us=row[3],
            )
        except (ValueError, json.JSONDecodeError) as exc:
            raise BotStoreError("BOT_RUNTIME_CORRUPT", "Grid çalışma durumu okunamadı.") from exc

    def save_grid_runtime(
        self,
        runtime: GridRuntime,
        *,
        events: tuple[BotEvent, ...] = (),
    ) -> None:
        """Persist one grid runner step atomically: snapshot plus events."""

        _validate_id(runtime.bot_id)
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.execute(
                    "INSERT OR REPLACE INTO grid_runtime VALUES (?,?,?,?,?)",
                    (
                        runtime.bot_id,
                        json.dumps(runtime.config, sort_keys=True, separators=(",", ":")),
                        json.dumps(runtime.snapshot, sort_keys=True, separators=(",", ":")),
                        runtime.last_bar_open_us,
                        runtime.updated_at_us,
                    ),
                )
                for event in events:
                    self.db.execute(
                        "INSERT INTO bot_events (bot_id, time_us, kind, detail_json) VALUES (?,?,?,?)",
                        (event.bot_id, event.time_us, event.kind, json.dumps(event.detail, sort_keys=True)),
                    )
                self.db.execute("COMMIT")
            except sqlite3.Error as exc:
                self.db.execute("ROLLBACK")
                raise BotStoreError("BOT_RUNTIME_WRITE_FAILED", "Grid çalışma durumu yazılamadı.") from exc

    def prune_bot_events(self, bot_id: str, *, keep: int = 2000) -> int:
        """Keep the newest `keep` events per bot; returns the removed count."""

        _validate_id(bot_id)
        if type(keep) is not int or keep < 100:
            raise BotStoreError("BOT_EVENTS_LIMIT_INVALID", "Saklama sayısı en az 100 olmalıdır.")
        with self._lock:
            cursor = self.db.execute(
                "DELETE FROM bot_events WHERE bot_id = ? AND id NOT IN "
                "(SELECT id FROM bot_events WHERE bot_id = ? ORDER BY id DESC LIMIT ?)",
                (bot_id, bot_id, keep),
            )
            return cursor.rowcount

    def list_deals(self, bot_id: str) -> tuple[BotDeal, ...]:
        _validate_id(bot_id)
        with self._lock:
            rows = self.db.execute(
                "SELECT bot_id, deal_sequence, started_at_us, closed_at_us, safety_orders_filled, profit, close_reason, manual_orders_filled, symbol "
                "FROM bot_deals WHERE bot_id = ? ORDER BY deal_sequence",
                (bot_id,),
            ).fetchall()
        return tuple(BotDeal(*row) for row in rows)

    def list_events(self, bot_id: str, *, limit: int) -> tuple[BotEvent, ...]:
        _validate_id(bot_id)
        if type(limit) is not int or not 1 <= limit <= 500:
            raise BotStoreError("BOT_EVENTS_LIMIT_INVALID", "Olay limiti 1-500 olmalıdır.")
        with self._lock:
            rows = self.db.execute(
                "SELECT bot_id, time_us, kind, detail_json FROM bot_events WHERE bot_id = ? ORDER BY id DESC LIMIT ?",
                (bot_id, limit),
            ).fetchall()
        return tuple(BotEvent(row[0], row[1], row[2], json.loads(row[3])) for row in rows)

    def save_portfolio_snapshot(self, time_us: int, equity: str, realized: str, unrealized: str) -> None:
        """Record one hourly portfolio point; same-hour rewrites replace."""

        if type(time_us) is not int or time_us < 0:
            raise BotStoreError("BOT_SNAPSHOT_INVALID", "Anlık görüntü zamanı geçersiz.")
        with self._lock:
            self.db.execute(
                "INSERT OR REPLACE INTO portfolio_snapshots VALUES (?,?,?,?)",
                (time_us, equity, realized, unrealized),
            )

    def latest_portfolio_snapshot_time(self) -> int | None:
        with self._lock:
            row = self.db.execute("SELECT MAX(time_us) FROM portfolio_snapshots").fetchone()
        return row[0] if row is not None else None

    def list_portfolio_snapshots(self, *, since_us: int | None = None) -> tuple[dict[str, object], ...]:
        """Oldest first; the equity chart reads this directly."""

        with self._lock:
            if since_us is None:
                rows = self.db.execute("SELECT time_us, equity, realized, unrealized FROM portfolio_snapshots ORDER BY time_us").fetchall()
            else:
                rows = self.db.execute(
                    "SELECT time_us, equity, realized, unrealized FROM portfolio_snapshots WHERE time_us >= ? ORDER BY time_us",
                    (since_us,),
                ).fetchall()
        return tuple({"time_us": row[0], "equity": row[1], "realized": row[2], "unrealized": row[3]} for row in rows)

    def prune_portfolio_snapshots(self, *, before_us: int) -> int:
        with self._lock:
            cursor = self.db.execute("DELETE FROM portfolio_snapshots WHERE time_us < ?", (before_us,))
        return cursor.rowcount

    @contextlib.contextmanager
    def guarded(self):
        """Share one reentrant guard across a read-compute-write step so the
        runner thread and deal-action requests cannot interleave and lose
        each other's runtime write. Reentrant: the per-method locks nest."""
        with self._lock:
            yield self

    @_locked
    def bump_revision(self, bot_id: str, *, expected_revision: int, now_us: int) -> BotRecord:
        """Revision bump without a lifecycle change: deal actions mutate
        runtime, not status, but concurrent readers must still see it."""
        current = self.get(bot_id)
        if current.archived_at_us is not None:
            raise BotStoreError("BOT_ARCHIVED", "Arşivlenmiş bot değiştirilemez.")
        return self._update(current, expected_revision, now_us)

    def list_all_deals(
        self, *, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> tuple[tuple["BotRecord", BotDeal], ...]:
        """Cross-bot deals, newest first; the unified deal list (W-B4)."""
        if status not in (None, "active", "closed"):
            raise BotStoreError("BOT_DEALS_STATUS_INVALID", "Durum active/closed olmalidir.")
        if type(limit) is not int or type(offset) is not int or not 1 <= limit <= 500 or offset < 0:
            raise BotStoreError("BOT_DEALS_PAGE_INVALID", "Sayfalama 1-500 limit, sifirdan offset.")
        query = (
            "SELECT b.bot_id, b.name, b.strategy_type, b.mode, b.symbol, b.strategy_json, b.budget,"
            " b.status, b.status_reason, b.revision, b.created_at_us, b.updated_at_us, b.archived_at_us,"
            " d.bot_id, d.deal_sequence, d.started_at_us, d.closed_at_us,"
            " d.safety_orders_filled, d.profit, d.close_reason, d.manual_orders_filled, d.symbol"
            " FROM bot_deals d JOIN bots b ON b.bot_id = d.bot_id"
        )
        params: list[object] = []
        if status == "active":
            query += " WHERE d.closed_at_us IS NULL"
        elif status == "closed":
            query += " WHERE d.closed_at_us IS NOT NULL"
        query += " ORDER BY d.started_at_us DESC, d.bot_id, d.deal_sequence LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._lock:
            rows = self.db.execute(query, params).fetchall()
        return tuple((_record(row[:13]), BotDeal(*row[13:])) for row in rows)

    def set_runner_status(self, bot_id: str, status: str, reason: str | None, *, now_us: int) -> BotRecord:
        """Runner-side status change (ERROR, or a reason note) without a
        client revision; still bumps `revision` so clients see the change."""
        if status not in BOT_STATUSES:
            raise BotStoreError("BOT_RECORD_INVALID", "Geçersiz durum.")
        with self._lock:
            current = self.get(bot_id)
            if current.status == status and current.status_reason == reason:
                return current
            return self._update(current, current.revision, now_us, status=status, status_reason=reason)

def _record(row: tuple) -> BotRecord:
    try:
        strategy = json.loads(row[5])
    except json.JSONDecodeError as exc:
        raise BotStoreError("BOT_RECORD_CORRUPT", "Bot kaydı okunamadı.") from exc
    if not isinstance(strategy, dict) or row[3] not in BOT_MODES or row[7] not in BOT_STATUSES:
        raise BotStoreError("BOT_RECORD_CORRUPT", "Bot kaydı okunamadı.")
    return BotRecord(
        bot_id=row[0],
        name=row[1],
        strategy_type=row[2],
        mode=row[3],
        symbol=row[4],
        strategy=strategy,
        budget=row[6],
        status=row[7],
        status_reason=row[8],
        revision=row[9],
        created_at_us=row[10],
        updated_at_us=row[11],
        archived_at_us=row[12],
    )
