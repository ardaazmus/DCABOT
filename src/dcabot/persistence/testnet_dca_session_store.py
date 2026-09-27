"""Durable store for `application/testnet_dca_session.py`'s `DcaSession`.

`testnet_dca_session.py` itself is a pure, in-memory orchestration layer
(its own docstring: "does not persist State/bindings durably -- a process
crash mid-deal loses the in-memory DCA session"). This module closes that
gap: it durably persists exactly the same `State`/`Config`/`OrderBinding`/
`applied_trade_ids` a `DcaSession` already carries, in a dedicated SQLite
file, protected by an in-process lock at the call site (matching this
project's other in-memory-plus-SQLite stores, e.g. `BOT_REGISTRY`).

This module does NOT place orders, call the venue, or touch credentials --
it only serializes/deserializes the session value object atomically.
"""

import json
from pathlib import Path
import sqlite3

from dcabot.application.testnet_dca_session import DcaSession, OrderBinding
from dcabot.domain.config import Config
from dcabot.domain.engine import State
from dcabot.domain.numbers import number
from dcabot.persistence.spot_binding_store import _decode_state, _state_payload


APPLICATION_ID = 0x44434153  # "DCAS"
SCHEMA_VERSION = 1


class TestnetDcaSessionStoreError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _validate_session_id(session_id: str) -> None:
    if (
        not isinstance(session_id, str)
        or not 1 <= len(session_id) <= 100
        or not all(ch.isalnum() or ch in "_-:." for ch in session_id)
    ):
        raise TestnetDcaSessionStoreError(
            "DCA_SESSION_ID_INVALID", "session_id 1-100 karakter, alfanumerik+_-:. olmalıdır."
        )


def _bindings_payload(bindings: tuple[OrderBinding, ...]) -> str:
    return json.dumps(
        [
            {
                "local_order_id": b.local_order_id,
                "role": b.role,
                "attempt_id": b.attempt_id,
                "venue_order_id": b.venue_order_id,
            }
            for b in bindings
        ],
        sort_keys=True,
        separators=(",", ":"),
    )


def _decode_bindings(payload: str) -> tuple[OrderBinding, ...]:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise TestnetDcaSessionStoreError(
            "DCA_SESSION_RECORD_CORRUPT", "Bindings JSON olarak okunamadı."
        ) from exc
    if not isinstance(raw, list):
        raise TestnetDcaSessionStoreError("DCA_SESSION_RECORD_CORRUPT", "Bindings liste olmalıdır.")
    try:
        return tuple(
            OrderBinding(
                local_order_id=item["local_order_id"],
                role=item["role"],
                attempt_id=item["attempt_id"],
                venue_order_id=item["venue_order_id"],
            )
            for item in raw
        )
    except (KeyError, TypeError) as exc:
        raise TestnetDcaSessionStoreError(
            "DCA_SESSION_RECORD_CORRUPT", "Binding alanları geçersiz."
        ) from exc


class TestnetDcaSessionStore:
    """Own one atomic SQLite file holding every durable `DcaSession`."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = sqlite3.connect(str(path), isolation_level=None, timeout=5)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self._initialize()
        except sqlite3.Error as exc:
            raise TestnetDcaSessionStoreError(
                "DCA_SESSION_STORE_UNAVAILABLE", "Testnet DCA session store açılamadı."
            ) from exc

    def _initialize(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS dca_sessions (
                session_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                raw_config TEXT NOT NULL,
                state_payload TEXT NOT NULL,
                bindings_payload TEXT NOT NULL,
                applied_trade_ids TEXT NOT NULL,
                created_at_us INTEGER NOT NULL,
                updated_at_us INTEGER NOT NULL
            )
            """
        )
        # `bot_id`/`starting_balance`/`mode` were added after this table's
        # first release -- an already-deployed local file predates them.
        # ALTER TABLE ADD COLUMN (not a second CREATE TABLE column) so an
        # existing store upgrades in place instead of failing to open.
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(dca_sessions)")}
        if "bot_id" not in columns:
            self.db.execute("ALTER TABLE dca_sessions ADD COLUMN bot_id TEXT")
        if "starting_balance" not in columns:
            self.db.execute("ALTER TABLE dca_sessions ADD COLUMN starting_balance TEXT")
        if "mode" not in columns:
            self.db.execute("ALTER TABLE dca_sessions ADD COLUMN mode TEXT")
            # Every session created before `mode` existed only ever went
            # through the real testnet /place flow -- backfill accordingly,
            # not left NULL/ambiguous.
            self.db.execute("UPDATE dca_sessions SET mode='TESTNET' WHERE mode IS NULL")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_dca_sessions_bot_id ON dca_sessions(bot_id)")

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "TestnetDcaSessionStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def create(
        self,
        session_id: str,
        session: DcaSession,
        raw_config: dict,
        *,
        now_us: int,
        bot_id: str | None = None,
        starting_balance: str | None = None,
        mode: str = "TESTNET",
    ) -> None:
        """Durably record a brand-new session; never overwrites an existing id.
        `bot_id` is an optional, purely-associative link (no economic
        meaning) letting `/api/bots/{bot_id}/*` aggregate this bot's own
        sessions -- CORE01's single-deal invariant is untouched, each
        session's own State/Config is still fully independent.
        `starting_balance` is an optional virtual "botUSD" balance for paper
        sessions -- a display-only anchor (`load()` never uses it in any
        engine.py computation); the session's own `realized_net_after_all_costs`
        is unaffected either way.
        `mode` (`TESTNET`|`PAPER`) is the explicit, required-at-creation
        answer to "can this session's `/place` ever send a real order" --
        added 2026-09-23 after the UI surfaced a real ambiguity: neither
        `starting_balance`'s presence nor `bindings` reliably told TESTNET
        and PAPER sessions apart (a PAPER session can paper-fill with no
        balance set; an unplaced TESTNET session has no bindings either)."""

        _validate_session_id(session_id)
        if not isinstance(session, DcaSession):
            raise TestnetDcaSessionStoreError("DCA_SESSION_INVALID", "session DcaSession olmalıdır.")
        if bot_id is not None and (not isinstance(bot_id, str) or not bot_id):
            raise TestnetDcaSessionStoreError("DCA_SESSION_BOT_ID_INVALID", "bot_id boş olmayan string ya da null olmalıdır.")
        if starting_balance is not None:
            try:
                if not isinstance(starting_balance, str) or number(starting_balance) <= 0:
                    raise ValueError
            except ValueError as exc:
                raise TestnetDcaSessionStoreError(
                    "DCA_SESSION_STARTING_BALANCE_INVALID", "starting_balance pozitif exact ondalık string ya da null olmalıdır."
                ) from exc
        if mode not in ("TESTNET", "PAPER"):
            raise TestnetDcaSessionStoreError("DCA_SESSION_MODE_INVALID", "mode yalnız 'TESTNET' ya da 'PAPER' olabilir.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute(
                "SELECT session_id FROM dca_sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if existing is not None:
                raise TestnetDcaSessionStoreError(
                    "DCA_SESSION_ALREADY_EXISTS", f"{session_id} zaten kayıtlı."
                )
            self.db.execute(
                "INSERT INTO dca_sessions "
                "(session_id, bot_id, starting_balance, mode, symbol, raw_config, state_payload, bindings_payload, "
                "applied_trade_ids, created_at_us, updated_at_us) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    session_id,
                    bot_id,
                    starting_balance,
                    mode,
                    session.symbol,
                    json.dumps(raw_config, sort_keys=True, separators=(",", ":")),
                    json.dumps(_state_payload(session.state), sort_keys=True, separators=(",", ":")),
                    _bindings_payload(session.bindings),
                    json.dumps(sorted(session.applied_trade_ids), separators=(",", ":")),
                    now_us,
                    now_us,
                ),
            )
            self.db.execute("COMMIT")
        except TestnetDcaSessionStoreError:
            self.db.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            self.db.execute("ROLLBACK")
            raise TestnetDcaSessionStoreError(
                "DCA_SESSION_STORE_UNAVAILABLE", "Testnet DCA session kaydedilemedi."
            ) from exc

    def save(self, session_id: str, session: DcaSession, *, now_us: int) -> None:
        """Overwrite an existing session's mutable projection. Caller (the
        process-wide lock holder) guarantees no concurrent writer."""

        _validate_session_id(session_id)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cursor = self.db.execute(
                "UPDATE dca_sessions SET state_payload=?, bindings_payload=?, "
                "applied_trade_ids=?, updated_at_us=? WHERE session_id=?",
                (
                    json.dumps(_state_payload(session.state), sort_keys=True, separators=(",", ":")),
                    _bindings_payload(session.bindings),
                    json.dumps(sorted(session.applied_trade_ids), separators=(",", ":")),
                    now_us,
                    session_id,
                ),
            )
            if cursor.rowcount == 0:
                raise TestnetDcaSessionStoreError(
                    "DCA_SESSION_NOT_FOUND", f"{session_id} kayıtlı değil."
                )
            self.db.execute("COMMIT")
        except TestnetDcaSessionStoreError:
            self.db.execute("ROLLBACK")
            raise
        except sqlite3.Error as exc:
            self.db.execute("ROLLBACK")
            raise TestnetDcaSessionStoreError(
                "DCA_SESSION_STORE_UNAVAILABLE", "Testnet DCA session güncellenemedi."
            ) from exc

    def load(self, session_id: str) -> DcaSession:
        _validate_session_id(session_id)
        row = self.db.execute(
            "SELECT symbol, raw_config, state_payload, bindings_payload, applied_trade_ids "
            "FROM dca_sessions WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if row is None:
            raise TestnetDcaSessionStoreError("DCA_SESSION_NOT_FOUND", f"{session_id} kayıtlı değil.")
        symbol, raw_config_json, state_json, bindings_json, trade_ids_json = row
        try:
            raw_config = json.loads(raw_config_json)
            config = Config.parse(raw_config)
            state = _decode_state(json.loads(state_json))
        except (json.JSONDecodeError, ValueError) as exc:
            raise TestnetDcaSessionStoreError(
                "DCA_SESSION_RECORD_CORRUPT", "Session kaydı doğrulanamadı."
            ) from exc
        bindings = _decode_bindings(bindings_json)
        try:
            trade_ids = frozenset(json.loads(trade_ids_json))
        except json.JSONDecodeError as exc:
            raise TestnetDcaSessionStoreError(
                "DCA_SESSION_RECORD_CORRUPT", "applied_trade_ids JSON olarak okunamadı."
            ) from exc
        return DcaSession(
            state=state,
            config=config,
            symbol=symbol,
            bindings=bindings,
            applied_trade_ids=trade_ids,
        )

    def get_starting_balance(self, session_id: str) -> str | None:
        _validate_session_id(session_id)
        row = self.db.execute(
            "SELECT starting_balance FROM dca_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            raise TestnetDcaSessionStoreError("DCA_SESSION_NOT_FOUND", f"{session_id} kayıtlı değil.")
        return row[0]

    def get_mode(self, session_id: str) -> str:
        _validate_session_id(session_id)
        row = self.db.execute(
            "SELECT mode FROM dca_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            raise TestnetDcaSessionStoreError("DCA_SESSION_NOT_FOUND", f"{session_id} kayıtlı değil.")
        return row[0] or "TESTNET"

    def list_ids(self) -> list[str]:
        rows = self.db.execute(
            "SELECT session_id FROM dca_sessions ORDER BY created_at_us"
        ).fetchall()
        return [row[0] for row in rows]

    def list_bot_ids(self) -> list[tuple[str, str | None]]:
        """Every session's (session_id, bot_id) pair, without loading full
        State/Config -- used for portfolio-wide aggregation across bots."""

        rows = self.db.execute(
            "SELECT session_id, bot_id FROM dca_sessions ORDER BY created_at_us"
        ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def list_ids_for_bot(self, bot_id: str) -> list[str]:
        if not isinstance(bot_id, str) or not bot_id:
            raise TestnetDcaSessionStoreError("DCA_SESSION_BOT_ID_INVALID", "bot_id boş olmayan string olmalıdır.")
        rows = self.db.execute(
            "SELECT session_id FROM dca_sessions WHERE bot_id=? ORDER BY created_at_us", (bot_id,)
        ).fetchall()
        return [row[0] for row in rows]
