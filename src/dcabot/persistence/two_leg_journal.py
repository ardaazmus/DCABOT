"""Durable journal for hedge two-leg sessions (Faz 6, LCR-09 frozen profile).

Stores only observed events — session start, accepted fills, explicit
recovery/timeout marks — and replays them through the pure in-memory
reducer. Never synthesizes a leg, never infers timeout from the clock.
"""
from pathlib import Path
import re
import sqlite3
from typing import Final

from dcabot.application.hedge_two_leg_contract import (
    HedgeTwoLegError,
    TwoLegState,
    new_hedge_position_identity,
)
from dcabot.application.two_leg_fill_projection import (
    LegFill,
    TwoLegFillProjection,
    accept_two_leg_fill,
    new_two_leg_projection,
    start_two_leg_projection,
)


APPLICATION_ID = 0x4443544C
SCHEMA_VERSION = 1

_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_TERMINALS: Final = (TwoLegState.RECOVERY_REQUIRED, TwoLegState.TIMEOUT)


class TwoLegJournalError(HedgeTwoLegError):
    """Raised when the journal cannot preserve its safety invariants."""


class TwoLegJournal:
    """Own one durable two-leg journal file; replay is the only reader."""

    def __init__(self, path: Path):
        self.path = _validate_path(path)
        existed = self.path.exists()
        try:
            self.db = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=rwc",
                uri=True,
                isolation_level=None,
                timeout=5,
            )
            self.db.execute("PRAGMA foreign_keys=ON")
            if existed:
                self._validate_existing()
            else:
                self._initialize()
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
        except TwoLegJournalError:
            self._close_after_open_failure()
            raise
        except (OSError, sqlite3.Error) as exc:
            self._close_after_open_failure()
            raise TwoLegJournalError(
                "TWO_LEG_JOURNAL_UNAVAILABLE", "Two-leg journal açılamadı."
            ) from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "TwoLegJournal":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def start(self, session_id: str) -> str:
        """Durably open the leg-A-pending boundary; creates no order."""
        _validate_session_id(session_id)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior = self.db.execute(
                "SELECT terminal FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if prior is not None:
                self.db.execute("COMMIT")
                return "DUPLICATE"
            self.db.execute(
                "INSERT INTO sessions (session_id, terminal) VALUES (?, NULL)",
                (session_id,),
            )
            self.db.execute("COMMIT")
            return "CREATED"
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def accept_fill(self, session_id: str, fill: LegFill) -> str:
        """Durably append one accepted fill after reducer validation."""
        _validate_session_id(session_id)
        if not isinstance(fill, LegFill):
            raise HedgeTwoLegError("TWO_LEG_FILL_INVALID", "Fill geçersiz.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            terminal = self._require_session_unlocked(session_id)
            if terminal is not None:
                raise HedgeTwoLegError(
                    "TWO_LEG_TRANSITION_INVALID",
                    "Terminal session yeni accepted fill kabul edemez.",
                )
            prior = self.db.execute(
                "SELECT leg_id, account_id, venue_profile, product_id, symbol,"
                " hedge_side, quantity, fill_status, event_time_us"
                " FROM fills WHERE session_id=? AND fill_id=?",
                (session_id, fill.fill_id),
            ).fetchone()
            if prior is not None:
                if tuple(prior) != _fill_values(fill):
                    raise TwoLegJournalError(
                        "TWO_LEG_JOURNAL_FILL_CONFLICT",
                        "Aynı fill kimliği farklı payload ile tekrarlandı.",
                    )
                self.db.execute("COMMIT")
                return "DUPLICATE"
            projection = self._replay_unlocked(session_id, terminal)
            next_projection, _ = accept_two_leg_fill(projection, fill)
            _ = next_projection
            self.db.execute(
                "INSERT INTO fills (session_id, fill_id, leg_id, account_id,"
                " venue_profile, product_id, symbol, hedge_side, quantity,"
                " fill_status, event_time_us)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (session_id, fill.fill_id, *_fill_values(fill)),
            )
            self.db.execute("COMMIT")
            return "ACCEPTED"
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def mark_recovery(self, session_id: str) -> TwoLegFillProjection:
        """Mark explicit operator-owned recovery; terminal, no auto action."""
        return self._mark_terminal(session_id, TwoLegState.RECOVERY_REQUIRED)

    def mark_timeout(self, session_id: str) -> TwoLegFillProjection:
        """Mark explicit timeout; never inferred from the clock."""
        return self._mark_terminal(session_id, TwoLegState.TIMEOUT)

    def replay(self, session_id: str) -> TwoLegFillProjection:
        """Fold stored events through the pure reducer; read-only."""
        _validate_session_id(session_id)
        row = self.db.execute(
            "SELECT terminal FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            raise TwoLegJournalError(
                "TWO_LEG_JOURNAL_UNKNOWN_SESSION", "Session journalda yok."
            )
        return self._replay_unlocked(session_id, row[0])

    def _mark_terminal(self, session_id: str, terminal: str) -> TwoLegFillProjection:
        _validate_session_id(session_id)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            current = self._require_session_unlocked(session_id)
            if current is not None:
                raise HedgeTwoLegError(
                    "TWO_LEG_TRANSITION_INVALID",
                    "Terminal session yeniden işaretlenemez.",
                )
            projection = self._replay_unlocked(session_id, None)
            if projection.state == TwoLegState.BOTH_ESTABLISHED:
                raise HedgeTwoLegError(
                    "TWO_LEG_STATE_INCONSISTENT",
                    "Recovery/timeout established projection üzerine uygulanamaz.",
                )
            self.db.execute(
                "UPDATE sessions SET terminal=? WHERE session_id=?",
                (terminal, session_id),
            )
            self.db.execute("COMMIT")
            return TwoLegFillProjection(
                state=terminal,
                leg_a_identity=projection.leg_a_identity,
                leg_b_identity=projection.leg_b_identity,
                leg_a_quantity=projection.leg_a_quantity,
                leg_b_quantity=projection.leg_b_quantity,
                leg_a_status=projection.leg_a_status,
                leg_b_status=projection.leg_b_status,
                fills=projection.fills,
            )
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _require_session_unlocked(self, session_id: str) -> str | None:
        row = self.db.execute(
            "SELECT terminal FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            raise TwoLegJournalError(
                "TWO_LEG_JOURNAL_UNKNOWN_SESSION", "Session journalda yok."
            )
        return row[0]

    def _replay_unlocked(
        self, session_id: str, terminal: str | None
    ) -> TwoLegFillProjection:
        rows = self.db.execute(
            "SELECT fill_id, leg_id, account_id, venue_profile, product_id,"
            " symbol, hedge_side, quantity, fill_status, event_time_us"
            " FROM fills WHERE session_id=? ORDER BY seq",
            (session_id,),
        ).fetchall()
        projection = start_two_leg_projection(new_two_leg_projection())
        for row in rows:
            fill = LegFill(
                fill_id=row[0],
                leg_id=row[1],
                position=new_hedge_position_identity(
                    account_id=row[2],
                    venue_profile=row[3],
                    product_id=row[4],
                    symbol=row[5],
                    position_mode="HEDGE",
                    hedge_side=row[6],
                ),
                quantity=row[7],
                fill_status=row[8],
                event_time_us=row[9],
            )
            projection, _ = accept_two_leg_fill(projection, fill)
        if terminal is not None:
            if terminal not in _TERMINALS:
                raise TwoLegJournalError(
                    "TWO_LEG_JOURNAL_TERMINAL_INVALID", "Terminal işareti geçersiz."
                )
            projection = TwoLegFillProjection(
                state=terminal,
                leg_a_identity=projection.leg_a_identity,
                leg_b_identity=projection.leg_b_identity,
                leg_a_quantity=projection.leg_a_quantity,
                leg_b_quantity=projection.leg_b_quantity,
                leg_a_status=projection.leg_a_status,
                leg_b_status=projection.leg_b_status,
                fills=projection.fills,
            )
        return projection

    def _validate_existing(self) -> None:
        app_id = self.db.execute("PRAGMA application_id").fetchone()[0]
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        tables = {
            row[0]
            for row in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if (
            app_id != APPLICATION_ID
            or version != SCHEMA_VERSION
            or not {"sessions", "fills"} <= tables
        ):
            raise TwoLegJournalError(
                "TWO_LEG_JOURNAL_SCHEMA_INVALID", "Journal şeması tanınmadı."
            )

    def _initialize(self) -> None:
        self.db.execute(f"PRAGMA application_id={APPLICATION_ID}")
        self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        self.db.execute(
            "CREATE TABLE sessions ("
            " session_id TEXT PRIMARY KEY,"
            " terminal TEXT"
            ") STRICT"
        )
        self.db.execute(
            "CREATE TABLE fills ("
            " seq INTEGER PRIMARY KEY AUTOINCREMENT,"
            " session_id TEXT NOT NULL REFERENCES sessions(session_id),"
            " fill_id TEXT NOT NULL,"
            " leg_id TEXT NOT NULL,"
            " account_id TEXT NOT NULL,"
            " venue_profile TEXT NOT NULL,"
            " product_id TEXT NOT NULL,"
            " symbol TEXT NOT NULL,"
            " hedge_side TEXT NOT NULL,"
            " quantity TEXT NOT NULL,"
            " fill_status TEXT NOT NULL,"
            " event_time_us INTEGER NOT NULL,"
            " UNIQUE (session_id, fill_id)"
            ") STRICT"
        )

    def _close_after_open_failure(self) -> None:
        try:
            self.db.close()
        except (AttributeError, sqlite3.Error):
            pass


def _validate_path(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TwoLegJournalError("TWO_LEG_JOURNAL_PATH_INVALID", "Journal path geçersiz.")
    return path


def _validate_session_id(session_id: object) -> None:
    if type(session_id) is not str or _IDENTIFIER.fullmatch(session_id) is None:
        raise TwoLegJournalError("TWO_LEG_JOURNAL_SESSION_INVALID", "Session kimliği geçersiz.")


def _fill_values(fill: LegFill) -> tuple[object, ...]:
    return (
        fill.leg_id,
        fill.position.account_id,
        fill.position.venue_profile,
        fill.position.product_id,
        fill.position.symbol,
        fill.position.hedge_side,
        fill.quantity,
        fill.fill_status,
        fill.event_time_us,
    )
