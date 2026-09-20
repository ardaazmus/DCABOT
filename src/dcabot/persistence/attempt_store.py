"""Dedicated SQLite store for redacted external-operation attempts."""

from dataclasses import replace
from pathlib import Path
import sqlite3

from dcabot.application.order_attempt import (
    AttemptOperation,
    AttemptState,
    OrderAttempt,
    OrderAttemptError,
    can_transition,
)


APPLICATION_ID = 0x4443414F
SCHEMA_VERSION = 1


class AttemptStoreError(OrderAttemptError):
    """Raised when the attempt store cannot preserve its safety invariants."""


class AttemptStore:
    """Own a dedicated durable store; it contains no raw request or secret."""

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
        except AttemptStoreError:
            self._close_after_open_failure()
            raise
        except (OSError, sqlite3.Error) as exc:
            self._close_after_open_failure()
            raise AttemptStoreError(
                "ATTEMPT_STORE_UNAVAILABLE", "Attempt store açılamadı."
            ) from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "AttemptStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def prepare(self, attempt: OrderAttempt) -> str:
        """Durably record PREPARED identity; never persist a raw request."""

        if not isinstance(attempt, OrderAttempt) or attempt.state is not AttemptState.PREPARED:
            raise AttemptStoreError("ATTEMPT_PREPARE_INVALID", "Yalnız PREPARED attempt kaydedilebilir.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior_row = self.db.execute(
                "SELECT * FROM attempts WHERE attempt_id=?", (attempt.attempt_id,)
            ).fetchone()
            if prior_row is not None:
                prior = _decode_row(prior_row)
                if prior == attempt:
                    self.db.execute("COMMIT")
                    return "DUPLICATE"
                raise AttemptStoreError(
                    "ATTEMPT_DUPLICATE_CONFLICT", "Aynı attempt kimliği farklı kayıtla kullanılamaz."
                )
            self.db.execute(
                "INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                _values(attempt),
            )
            self.db.execute("COMMIT")
            return "CREATED"
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def persist(self, attempt_id: str, *, now_us: int) -> OrderAttempt:
        """Atomically promote PREPARED to durable PERSISTED before any send."""

        return self._transition(
            attempt_id,
            current=AttemptState.PREPARED,
            target=AttemptState.PERSISTED,
            now_us=now_us,
        )

    def mark_sending(self, attempt_id: str, *, now_us: int) -> OrderAttempt:
        """Allow sending only from a durable PERSISTED record."""

        return self._transition(
            attempt_id,
            current=AttemptState.PERSISTED,
            target=AttemptState.SENDING,
            now_us=now_us,
            send_started_at_us=now_us,
        )

    def mark_acknowledged(
        self, attempt_id: str, *, now_us: int, venue_order_id: int | None = None
    ) -> OrderAttempt:
        return self._transition(
            attempt_id,
            current=AttemptState.SENDING,
            target=AttemptState.ACKNOWLEDGED,
            now_us=now_us,
            venue_order_id=venue_order_id,
        )

    def mark_rejected(
        self, attempt_id: str, *, now_us: int, reason: str, venue_error_code: int | None = None
    ) -> OrderAttempt:
        return self._transition(
            attempt_id,
            current=AttemptState.SENDING,
            target=AttemptState.REJECTED,
            now_us=now_us,
            terminal_reason=reason,
            venue_error_code=venue_error_code,
        )

    def mark_unknown(self, attempt_id: str, *, now_us: int, reason: str) -> OrderAttempt:
        return self._transition(
            attempt_id,
            current=AttemptState.SENDING,
            target=AttemptState.UNKNOWN,
            now_us=now_us,
            terminal_reason=reason,
        )

    def begin_reconciliation(self, attempt_id: str, *, now_us: int) -> OrderAttempt:
        return self._transition(
            attempt_id,
            current=AttemptState.UNKNOWN,
            target=AttemptState.RECONCILING,
            now_us=now_us,
            last_recovery_at_us=now_us,
            recovery_query_count=1,
        )

    def mark_reconciled_acknowledged(
        self, attempt_id: str, *, now_us: int, venue_order_id: int
    ) -> OrderAttempt:
        return self._transition(
            attempt_id,
            current=AttemptState.RECONCILING,
            target=AttemptState.ACKNOWLEDGED,
            now_us=now_us,
            venue_order_id=venue_order_id,
        )

    def mark_reconciliation_unresolved(
        self, attempt_id: str, *, now_us: int, reason: str
    ) -> OrderAttempt:
        return self._transition(
            attempt_id,
            current=AttemptState.RECONCILING,
            target=AttemptState.UNRESOLVED,
            now_us=now_us,
            terminal_reason=reason,
        )

    def recover_after_restart(self, *, now_us: int) -> tuple[OrderAttempt, ...]:
        """Quarantine every in-flight send as UNKNOWN after process restart."""

        self.db.execute("BEGIN IMMEDIATE")
        try:
            rows = self.db.execute(
                "SELECT * FROM attempts WHERE state=? ORDER BY attempt_id",
                (AttemptState.SENDING.value,),
            ).fetchall()
            recovered = []
            for row in rows:
                current = _decode_row(row)
                updated = replace(
                    current,
                    state=AttemptState.UNKNOWN,
                    last_transition_at_us=now_us,
                    terminal_reason="RESTART_DURING_SEND",
                )
                self.db.execute(
                    "UPDATE attempts SET state=?, last_transition_at_us=?, terminal_reason=? "
                    "WHERE attempt_id=? AND state=?",
                    (
                        updated.state.value,
                        updated.last_transition_at_us,
                        updated.terminal_reason,
                        updated.attempt_id,
                        current.state.value,
                    ),
                )
                recovered.append(updated)
            self.db.execute("COMMIT")
            return tuple(recovered)
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def get(self, attempt_id: str) -> OrderAttempt:
        row = self.db.execute(
            "SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)
        ).fetchone()
        if row is None:
            raise AttemptStoreError("ATTEMPT_NOT_FOUND", "Attempt bulunamadı.")
        return _decode_row(row)

    def count(self) -> int:
        return self.db.execute("SELECT count(*) FROM attempts").fetchone()[0]

    def count_blocking_attempts(self) -> int:
        """Count attempts that prevent a reconciled economic state."""

        states = tuple(
            state.value
            for state in (
                AttemptState.UNKNOWN,
                AttemptState.RECONCILING,
                AttemptState.UNRESOLVED,
            )
        )
        placeholders = ",".join("?" for _ in states)
        return self.db.execute(
            f"SELECT count(*) FROM attempts WHERE state IN ({placeholders})", states
        ).fetchone()[0]

    def list_resolvable_attempts(self) -> tuple[OrderAttempt, ...]:
        """List blocking attempts that a fresh lookup can still resolve.

        UNRESOLVED is intentionally excluded: `can_transition` gives it no
        outgoing edge, so `reconcile_attempt` can never move it and it is not
        actionable by a REST catch-up pass — it stays a permanent block until
        an operator investigates out of band.
        """

        states = (AttemptState.UNKNOWN.value, AttemptState.RECONCILING.value)
        rows = self.db.execute(
            "SELECT * FROM attempts WHERE state IN (?,?) ORDER BY attempt_id", states
        ).fetchall()
        return tuple(_decode_row(row) for row in rows)

    def _transition(
        self,
        attempt_id: str,
        *,
        current: AttemptState,
        target: AttemptState,
        now_us: int,
        **changes: object,
    ) -> OrderAttempt:
        if not can_transition(current, target):
            raise AttemptStoreError("ATTEMPT_TRANSITION_INVALID", "Attempt state geçişi tanımsız.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior = self.get(attempt_id)
            if prior.state is not current:
                raise AttemptStoreError(
                    "ATTEMPT_STATE_CONFLICT", "Attempt beklenen state içinde değil."
                )
            updated = replace(
                prior,
                state=target,
                last_transition_at_us=now_us,
                **changes,
            )
            self.db.execute(
                "UPDATE attempts SET state=?, last_transition_at_us=?, send_started_at_us=?, "
                "venue_order_id=?, venue_error_code=?, recovery_query_count=?, last_recovery_at_us=?, "
                "terminal_reason=? WHERE attempt_id=? AND state=?",
                (
                    updated.state.value,
                    updated.last_transition_at_us,
                    updated.send_started_at_us,
                    updated.venue_order_id,
                    updated.venue_error_code,
                    updated.recovery_query_count,
                    updated.last_recovery_at_us,
                    updated.terminal_reason,
                    updated.attempt_id,
                    current.value,
                ),
            )
            self.db.execute("COMMIT")
            return updated
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(self) -> None:
        self.db.executescript(
            f"""
            BEGIN IMMEDIATE;
            PRAGMA application_id={APPLICATION_ID};
            PRAGMA user_version={SCHEMA_VERSION};
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO metadata VALUES
                ('store', 'offline-attempts-1'),
                ('scope', 'REDACTED_EXTERNAL_OPERATION_ATTEMPTS_ONLY');
            CREATE TABLE attempts(
                attempt_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                venue TEXT NOT NULL,
                operation TEXT NOT NULL,
                symbol TEXT NOT NULL,
                client_order_id TEXT,
                request_fingerprint_sha256 TEXT NOT NULL,
                capability_snapshot_hash TEXT NOT NULL,
                filter_snapshot_hash TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at_us INTEGER NOT NULL,
                last_transition_at_us INTEGER NOT NULL,
                send_started_at_us INTEGER,
                venue_order_id INTEGER,
                venue_event_time_ms INTEGER,
                venue_transaction_time_ms INTEGER,
                http_status INTEGER,
                venue_error_code INTEGER,
                recovery_query_count INTEGER NOT NULL,
                last_recovery_at_us INTEGER,
                terminal_reason TEXT
            );
            COMMIT;
            """
        )

    def _validate_existing(self) -> None:
        if (
            self.db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
            or self.db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
        ):
            raise AttemptStoreError("ATTEMPT_STORE_UNSUPPORTED", "Attempt store şeması desteklenmiyor.")
        metadata = dict(self.db.execute("SELECT key, value FROM metadata"))
        if metadata != {
            "store": "offline-attempts-1",
            "scope": "REDACTED_EXTERNAL_OPERATION_ATTEMPTS_ONLY",
        }:
            raise AttemptStoreError("ATTEMPT_STORE_METADATA_INVALID", "Attempt store metadata geçersiz.")
        try:
            self.db.execute("SELECT 1 FROM attempts LIMIT 1")
        except sqlite3.Error as exc:
            raise AttemptStoreError("ATTEMPT_STORE_UNSUPPORTED", "Attempt tablosu eksik.") from exc

    def _close_after_open_failure(self) -> None:
        if hasattr(self, "db"):
            self.db.close()


def _values(attempt: OrderAttempt) -> tuple[object, ...]:
    return (
        attempt.attempt_id,
        attempt.run_id,
        attempt.venue,
        attempt.operation.value,
        attempt.symbol,
        attempt.client_order_id,
        attempt.request_fingerprint_sha256,
        attempt.capability_snapshot_hash,
        attempt.filter_snapshot_hash,
        attempt.state.value,
        attempt.created_at_us,
        attempt.last_transition_at_us,
        attempt.send_started_at_us,
        attempt.venue_order_id,
        attempt.venue_event_time_ms,
        attempt.venue_transaction_time_ms,
        attempt.http_status,
        attempt.venue_error_code,
        attempt.recovery_query_count,
        attempt.last_recovery_at_us,
        attempt.terminal_reason,
    )


def _decode_row(row: tuple[object, ...]) -> OrderAttempt:
    try:
        return OrderAttempt(
            attempt_id=row[0],
            run_id=row[1],
            venue=row[2],
            operation=AttemptOperation(row[3]),
            symbol=row[4],
            client_order_id=row[5],
            request_fingerprint_sha256=row[6],
            capability_snapshot_hash=row[7],
            filter_snapshot_hash=row[8],
            state=AttemptState(row[9]),
            created_at_us=row[10],
            last_transition_at_us=row[11],
            send_started_at_us=row[12],
            venue_order_id=row[13],
            venue_event_time_ms=row[14],
            venue_transaction_time_ms=row[15],
            http_status=row[16],
            venue_error_code=row[17],
            recovery_query_count=row[18],
            last_recovery_at_us=row[19],
            terminal_reason=row[20],
        )
    except (IndexError, TypeError, ValueError, OrderAttemptError) as exc:
        raise AttemptStoreError("ATTEMPT_RECORD_CORRUPT", "Attempt kaydı doğrulanamadı.") from exc


def _validate_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or _is_linked(candidate) or _is_linked(resolved.parent):
        raise AttemptStoreError("ATTEMPT_STORE_PATH_INVALID", "Attempt store backup/linked path üzerinde olamaz.")
    if not resolved.parent.is_dir() or (candidate.exists() and not candidate.is_file()):
        raise AttemptStoreError("ATTEMPT_STORE_PATH_INVALID", "Attempt store yolu geçersiz.")
    return candidate


def _is_linked(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())
