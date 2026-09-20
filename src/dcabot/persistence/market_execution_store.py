"""Durable offline replay for exact MARKET economics and redacted identity."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3

from dcabot.application.market_base_quantity import (
    MarketBaseExecution,
    MarketExecutionOutcome,
    MarketExecutionStatus,
    MarketFill,
    create_market_base_execution,
)
from dcabot.application.market_execution_reconciliation import (
    MarketExecutionReconciliationBinding,
)


APPLICATION_ID = 0x44434D45
SCHEMA_VERSION = 1
MAX_BINDINGS = 1_000


class MarketExecutionStoreError(ValueError):
    """Raised when the durable MARKET projection cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class MarketExecutionReplay:
    """Validated MARKET economics and redacted identity links."""

    execution: MarketBaseExecution
    bindings: tuple[MarketExecutionReconciliationBinding, ...]


class MarketExecutionStore:
    """Own one bounded SQLite projection without core or order authority."""

    def __init__(self, path: Path, db: sqlite3.Connection) -> None:
        self.path = path
        self.db = db

    @classmethod
    def create(cls, path: Path, execution: MarketBaseExecution) -> "MarketExecutionStore":
        validated = _validate_path(path)
        if validated.exists():
            raise MarketExecutionStoreError("MARKET_STORE_EXISTS", "MARKET store mevcut dosyanın üzerine yazamaz.")
        _validate_execution(execution)
        try:
            with validated.open("xb"):
                pass
            db = _connect(validated)
            store = cls(validated, db)
            store._initialize(execution)
            return store
        except MarketExecutionStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise MarketExecutionStoreError("MARKET_STORE_UNAVAILABLE", "MARKET store açılamadı.") from exc

    @classmethod
    def open(cls, path: Path) -> "MarketExecutionStore":
        validated = _validate_path(path)
        if not validated.is_file():
            raise MarketExecutionStoreError("MARKET_STORE_MISSING", "MARKET store bulunamadı.")
        try:
            db = _connect(validated)
            if (
                db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
            ):
                raise MarketExecutionStoreError("MARKET_STORE_UNSUPPORTED", "MARKET store şeması desteklenmiyor.")
            metadata = dict(db.execute("SELECT key, value FROM metadata"))
            if metadata.get("store") != "offline-market-execution-1" or metadata.get(
                "scope"
            ) != "DURABLE_MARKET_ECONOMIC_REPLAY":
                raise MarketExecutionStoreError("MARKET_STORE_METADATA_INVALID", "MARKET store metadata geçersiz.")
            store = cls(validated, db)
            store._load_unlocked()
            return store
        except MarketExecutionStoreError:
            if "db" in locals():
                db.close()
            raise
        except (OSError, sqlite3.Error) as exc:
            if "db" in locals():
                db.close()
            raise MarketExecutionStoreError("MARKET_STORE_UNAVAILABLE", "MARKET store açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "MarketExecutionStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def save(
        self,
        execution: MarketBaseExecution,
        binding: MarketExecutionReconciliationBinding | None = None,
    ) -> MarketExecutionOutcome:
        """Atomically save a valid successor and optionally one identity binding."""

        _validate_execution(execution)
        if binding is not None:
            _validate_binding(binding, execution)
        state_payload = _canonical(_execution_payload(execution))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT state_payload, state_hash FROM market_execution_state WHERE order_id=?",
                (execution.order_id,),
            ).fetchone()
            if row is None:
                raise MarketExecutionStoreError("MARKET_STORE_STATE_MISSING", "MARKET başlangıç state’i bulunamadı.")
            prior = _decode_checked_execution(row[0], row[1])
            _validate_successor(prior, execution)
            outcome = MarketExecutionOutcome.ACCEPTED if prior != execution else MarketExecutionOutcome.DUPLICATE
            if binding is not None:
                binding_payload = _canonical(_binding_payload(binding))
                existing = self.db.execute(
                    "SELECT binding_payload FROM market_bindings WHERE venue_event_id=?",
                    (binding.venue_event_id,),
                ).fetchone()
                if existing is not None:
                    if existing[0] != binding_payload:
                        raise MarketExecutionStoreError(
                            "MARKET_STORE_BINDING_CONFLICT", "Aynı venue event kimliği farklı binding ile kullanılamaz."
                        )
                    outcome = MarketExecutionOutcome.DUPLICATE
                else:
                    for column, value in (
                        ("spot_event_id", binding.spot_event_id),
                        ("execution_id", binding.execution_id),
                    ):
                        conflict = self.db.execute(
                            f"SELECT 1 FROM market_bindings WHERE {column}=?", (value,)
                        ).fetchone()
                        if conflict is not None:
                            raise MarketExecutionStoreError(
                                "MARKET_STORE_BINDING_CONFLICT", "Binding kimliği farklı bir MARKET kaydına bağlı."
                            )
                    if prior == execution or binding.fill in prior.fills:
                        raise MarketExecutionStoreError(
                            "MARKET_STORE_BINDING_STATE_INVALID", "Yeni binding yeni bir exact fill state’i gerektirir."
                        )
                    binding_count = self.db.execute("SELECT COUNT(*) FROM market_bindings").fetchone()[0]
                    if binding_count >= MAX_BINDINGS:
                        raise MarketExecutionStoreError("MARKET_STORE_BINDING_LIMIT", "MARKET binding sınırına ulaşıldı.")
                    self.db.execute(
                        "INSERT INTO market_bindings(venue_event_id, spot_event_id, execution_id, binding_payload, binding_hash) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            binding.venue_event_id,
                            binding.spot_event_id,
                            binding.execution_id,
                            binding_payload,
                            _digest(binding_payload),
                        ),
                    )
                    outcome = MarketExecutionOutcome.ACCEPTED
            if prior != execution:
                self.db.execute(
                    "UPDATE market_execution_state SET state_payload=?, state_hash=? WHERE order_id=?",
                    (state_payload, _digest(state_payload), execution.order_id),
                )
            self.db.execute("COMMIT")
            return outcome
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def load(self) -> MarketExecutionReplay:
        """Replay the MARKET projection without creating core events."""

        self.db.execute("BEGIN")
        try:
            result = self._load_unlocked()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(self, execution: MarketBaseExecution) -> None:
        payload = _canonical(_execution_payload(execution))
        self.db.executescript(
            f"""
            BEGIN IMMEDIATE;
            PRAGMA application_id={APPLICATION_ID};
            PRAGMA user_version={SCHEMA_VERSION};
            CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE market_execution_state(
                order_id TEXT PRIMARY KEY,
                state_payload TEXT NOT NULL,
                state_hash TEXT NOT NULL
            );
            CREATE TABLE market_bindings(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                venue_event_id TEXT UNIQUE NOT NULL,
                spot_event_id TEXT UNIQUE NOT NULL,
                execution_id TEXT UNIQUE NOT NULL,
                binding_payload TEXT NOT NULL,
                binding_hash TEXT NOT NULL
            );
            INSERT INTO metadata(key, value) VALUES
                ('store', 'offline-market-execution-1'),
                ('scope', 'DURABLE_MARKET_ECONOMIC_REPLAY');
            INSERT INTO market_execution_state VALUES
                ('{_sql_text(execution.order_id)}', '{_sql_text(payload)}', '{_digest(payload)}');
            COMMIT;
            """
        )

    def _load_unlocked(self) -> MarketExecutionReplay:
        row = self.db.execute(
            "SELECT state_payload, state_hash FROM market_execution_state"
        ).fetchall()
        if len(row) != 1:
            raise MarketExecutionStoreError("MARKET_STORE_STATE_INVALID", "Tek MARKET state kaydı bekleniyordu.")
        execution = _decode_checked_execution(row[0][0], row[0][1])
        bindings = []
        for payload, payload_hash in self.db.execute(
            "SELECT binding_payload, binding_hash FROM market_bindings ORDER BY sequence"
        ):
            if _digest(payload) != payload_hash:
                raise MarketExecutionStoreError("MARKET_STORE_RECORD_CORRUPT", "MARKET binding checksum doğrulanamadı.")
            try:
                binding = _decode_binding(json.loads(payload))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise MarketExecutionStoreError("MARKET_STORE_RECORD_CORRUPT", "MARKET binding payload geçersiz.") from exc
            _validate_binding(binding, execution)
            bindings.append(binding)
        return MarketExecutionReplay(execution, tuple(bindings))


def _validate_execution(execution: object) -> None:
    if not isinstance(execution, MarketBaseExecution):
        raise MarketExecutionStoreError("MARKET_STORE_EXECUTION_INVALID", "MARKET execution güvenli tipte değil.")
    if execution.status is MarketExecutionStatus.NEW and execution.fills:
        raise MarketExecutionStoreError("MARKET_STORE_STATE_INVALID", "Fill taşıyan state NEW olamaz.")
    if execution.status is MarketExecutionStatus.PARTIALLY_FILLED and not execution.fills:
        raise MarketExecutionStoreError("MARKET_STORE_STATE_INVALID", "PARTIALLY_FILLED state fill taşımalıdır.")
    if execution.status is MarketExecutionStatus.FILLED and execution.remaining_quantity != "0":
        raise MarketExecutionStoreError("MARKET_STORE_STATE_INVALID", "FILLED state residual taşıyamaz.")


def _validate_binding(binding: object, execution: MarketBaseExecution) -> None:
    if not isinstance(binding, MarketExecutionReconciliationBinding):
        raise MarketExecutionStoreError("MARKET_STORE_BINDING_INVALID", "MARKET binding güvenli tipte değil.")
    if (
        binding.market_order_id != execution.order_id
        or binding.spot_order_id != execution.order_id
        or binding.execution_id != binding.fill.execution_id
        or binding.fill not in execution.fills
        or not isinstance(binding.venue_order_id, int)
        or isinstance(binding.venue_order_id, bool)
        or binding.venue_order_id <= 0
    ):
        raise MarketExecutionStoreError("MARKET_STORE_BINDING_INVALID", "MARKET binding execution ile eşleşmiyor.")


def _validate_successor(prior: MarketBaseExecution, current: MarketBaseExecution) -> None:
    if (
        prior.order_id,
        prior.symbol,
        prior.side,
        prior.requested_quantity,
        prior.reference_price,
        prior.max_slippage_bps,
    ) != (
        current.order_id,
        current.symbol,
        current.side,
        current.requested_quantity,
        current.reference_price,
        current.max_slippage_bps,
    ):
        raise MarketExecutionStoreError("MARKET_STORE_STATE_CONFLICT", "MARKET immutable execution kimliği değiştirilemez.")
    if prior.status in {
        MarketExecutionStatus.FILLED,
        MarketExecutionStatus.CANCELED,
        MarketExecutionStatus.EXPIRED,
    } and current != prior:
        raise MarketExecutionStoreError("MARKET_STORE_STATE_CONFLICT", "Terminal MARKET state değiştirilemez.")
    if tuple(current.fills[: len(prior.fills)]) != prior.fills:
        raise MarketExecutionStoreError("MARKET_STORE_STATE_CONFLICT", "MARKET fill geçmişi geriye dönük değiştirilemez.")


def _execution_payload(execution: MarketBaseExecution) -> dict[str, object]:
    return {
        "order_id": execution.order_id,
        "symbol": execution.symbol,
        "side": execution.side.value,
        "requested_quantity": execution.requested_quantity,
        "reference_price": execution.reference_price,
        "max_slippage_bps": execution.max_slippage_bps,
        "status": execution.status.value,
        "fills": [_fill_payload(fill) for fill in execution.fills],
    }


def _fill_payload(fill: MarketFill) -> dict[str, str]:
    return {
        "execution_id": fill.execution_id,
        "base_quantity": fill.base_quantity,
        "quote_quantity": fill.quote_quantity,
        "effective_price": fill.effective_price,
        "fee": fill.fee,
        "fee_asset": fill.fee_asset,
    }


def _binding_payload(binding: MarketExecutionReconciliationBinding) -> dict[str, object]:
    return {
        "venue_event_id": binding.venue_event_id,
        "venue_order_id": binding.venue_order_id,
        "spot_event_id": binding.spot_event_id,
        "spot_order_id": binding.spot_order_id,
        "market_order_id": binding.market_order_id,
        "execution_id": binding.execution_id,
        "fill": _fill_payload(binding.fill),
    }


def _decode_checked_execution(payload: str, payload_hash: str) -> MarketBaseExecution:
    if _digest(payload) != payload_hash:
        raise MarketExecutionStoreError("MARKET_STORE_RECORD_CORRUPT", "MARKET state checksum doğrulanamadı.")
    try:
        data = json.loads(payload)
        execution = create_market_base_execution(
            order_id=data["order_id"],
            symbol=data["symbol"],
            side=data["side"],
            requested_quantity=data["requested_quantity"],
            reference_price=data["reference_price"],
            max_slippage_bps=data["max_slippage_bps"],
        )
        for item in data["fills"]:
            fill = _decode_fill(item)
            accepted = execution.apply_fill(
                execution_id=fill.execution_id,
                base_quantity=fill.base_quantity,
                quote_quantity=fill.quote_quantity,
                fee=fill.fee,
                fee_asset=fill.fee_asset,
            )
            if accepted.execution.fills[-1] != fill:
                raise ValueError("fill normalization mismatch")
            execution = accepted.execution
        status = MarketExecutionStatus(data["status"])
        if status is not MarketExecutionStatus.PARTIALLY_FILLED and status is not MarketExecutionStatus.NEW:
            execution = execution.close(status)
        elif status is MarketExecutionStatus.NEW and execution.fills:
            raise ValueError("NEW with fills")
        return execution
    except MarketExecutionStoreError:
        raise
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MarketExecutionStoreError("MARKET_STORE_RECORD_CORRUPT", "MARKET state payload geçersiz.") from exc


def _decode_fill(data: object) -> MarketFill:
    if not isinstance(data, dict):
        raise ValueError("fill object expected")
    return MarketFill(
        execution_id=data["execution_id"],
        base_quantity=data["base_quantity"],
        quote_quantity=data["quote_quantity"],
        effective_price=data["effective_price"],
        fee=data["fee"],
        fee_asset=data["fee_asset"],
    )


def _decode_binding(data: object) -> MarketExecutionReconciliationBinding:
    if not isinstance(data, dict):
        raise ValueError("binding object expected")
    return MarketExecutionReconciliationBinding(
        venue_event_id=data["venue_event_id"],
        venue_order_id=data["venue_order_id"],
        spot_event_id=data["spot_event_id"],
        spot_order_id=data["spot_order_id"],
        market_order_id=data["market_order_id"],
        execution_id=data["execution_id"],
        fill=_decode_fill(data["fill"]),
    )


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sql_text(value: str) -> str:
    return value.replace("'", "''")


def _validate_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or any(
        item.is_symlink() or bool(getattr(item, "is_junction", lambda: False)())
        for item in (candidate, *candidate.parents)
    ):
        raise MarketExecutionStoreError("MARKET_STORE_PATH_UNSAFE", "MARKET store backup/linked path üzerinde olamaz.")
    if candidate.exists() and not candidate.is_file():
        raise MarketExecutionStoreError("MARKET_STORE_PATH_INVALID", "MARKET store yolu dosya olmalıdır.")
    if not resolved.parent.is_dir():
        raise MarketExecutionStoreError("MARKET_STORE_PATH_INVALID", "MARKET store parent yolu bulunmalıdır.")
    return candidate


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=5)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db
