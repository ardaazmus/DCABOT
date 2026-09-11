"""Persistent, exact shared-account reservation ledger for local execution."""

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from dcabot.application.account_reservation import (
    AccountCapacity,
    AccountReservation,
    AccountReservationError,
)
from dcabot.application.shared_account_identity import new_shared_account_identity
from dcabot.domain.numbers import Q, bounded, exact_text, positive


LEDGER_APPLICATION_ID = 0x44434152
LEDGER_SCHEMA_VERSION = 1
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


@dataclass(frozen=True, slots=True)
class ReservationCommit:
    """Exact result persisted with one successful reservation transition."""

    reservation_id: str
    account_id: str
    asset: str
    amount: str
    version_before: int
    version_after: int
    active_reserved_after: str
    available_after: str


class ReservationLedgerError(AccountReservationError):
    """Raised when the persistent reservation ledger cannot commit safely."""


class ReservationLedger:
    """Own a dedicated SQLite ledger with atomic account-version transitions."""

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
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            if not existed:
                self._initialize()
        except ReservationLedgerError:
            self._close_after_open_failure()
            raise
        except (OSError, sqlite3.Error) as exc:
            self._close_after_open_failure()
            raise ReservationLedgerError(
                "ACCOUNT_LEDGER_UNAVAILABLE", "Account reservation ledger açılamadı."
            ) from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "ReservationLedger":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def initialize_capacity(self, capacity: AccountCapacity) -> None:
        """Create one capacity or accept the identical already-initialized value."""

        if not isinstance(capacity, AccountCapacity):
            raise ReservationLedgerError(
                "ACCOUNT_CAPACITY_INVALID", "Account capacity geçersiz."
            )
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT amount, version FROM account_capacities WHERE account_id=? AND asset=?",
                (capacity.account_id, capacity.asset),
            ).fetchone()
            if row is None:
                self.db.execute(
                    "INSERT INTO account_capacities(account_id, asset, amount, version) VALUES (?, ?, ?, ?)",
                    (capacity.account_id, capacity.asset, capacity.amount, capacity.version),
                )
            elif row != (capacity.amount, capacity.version):
                raise ReservationLedgerError(
                    "ACCOUNT_CAPACITY_CONFLICT",
                    "Mevcut kapasite farklı değerle yeniden başlatılamaz.",
                )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def get_capacity(self, account_id: str, asset: str) -> AccountCapacity:
        """Read one capacity snapshot without changing its version."""

        _validate_identifier(account_id, "ACCOUNT_CAPACITY_IDENTITY_INVALID")
        _validate_identifier(asset, "ACCOUNT_CAPACITY_ASSET_INVALID")
        row = self.db.execute(
            "SELECT amount, version FROM account_capacities WHERE account_id=? AND asset=?",
            (account_id, asset),
        ).fetchone()
        if row is None:
            raise ReservationLedgerError(
                "ACCOUNT_CAPACITY_MISSING", "Account kapasitesi bulunamadı."
            )
        return AccountCapacity(account_id, asset, row[0], row[1])

    def list_active(self, account_id: str, asset: str) -> tuple[AccountReservation, ...]:
        """Read the exact active reservation set for one account and asset."""

        _validate_identifier(account_id, "ACCOUNT_CAPACITY_IDENTITY_INVALID")
        _validate_identifier(asset, "ACCOUNT_CAPACITY_ASSET_INVALID")
        rows = self.db.execute(
            "SELECT reservation_id, product_id, position_mode, deal_id, allocation_id, amount "
            "FROM account_reservations WHERE account_id=? AND asset=? AND status='ACTIVE' "
            "ORDER BY reservation_id",
            (account_id, asset),
        ).fetchall()
        return tuple(
            AccountReservation(
                reservation_id=row[0],
                owner=new_shared_account_identity(
                    account_id, row[1], row[2], row[3], row[4]
                ),
                asset=asset,
                amount=row[5],
            )
            for row in rows
        )

    def reserve(
        self, reservation: AccountReservation, *, expected_version: int
    ) -> ReservationCommit:
        """Atomically reserve capacity or fail without a partial transition."""

        if not isinstance(reservation, AccountReservation):
            raise ReservationLedgerError(
                "ACCOUNT_RESERVATION_INPUT_INVALID", "Reservation geçersiz."
            )
        if type(expected_version) is not int or expected_version < 0:
            raise ReservationLedgerError(
                "ACCOUNT_VERSION_CONFLICT", "Expected account version geçersiz."
            )
        self.db.execute("BEGIN IMMEDIATE")
        try:
            capacity_row = self.db.execute(
                "SELECT amount, version FROM account_capacities WHERE account_id=? AND asset=?",
                (reservation.owner.account_id, reservation.asset),
            ).fetchone()
            if capacity_row is None:
                raise ReservationLedgerError(
                    "ACCOUNT_CAPACITY_MISSING", "Account kapasitesi bulunamadı."
                )

            duplicate = self.db.execute(
                "SELECT account_id, product_id, position_mode, deal_id, allocation_id, asset, amount, "
                "version_before, version_after, active_reserved_after, available_after "
                "FROM account_reservations WHERE reservation_id=?",
                (reservation.reservation_id,),
            ).fetchone()
            if duplicate is not None:
                if not _same_reservation(reservation, duplicate):
                    raise ReservationLedgerError(
                        "ACCOUNT_RESERVATION_DUPLICATE_CONFLICT",
                        "Aynı reservation kimliği farklı payload ile kullanılamaz.",
                    )
                self.db.execute("COMMIT")
                return ReservationCommit(
                    reservation_id=reservation.reservation_id,
                    account_id=duplicate[0],
                    asset=duplicate[5],
                    amount=duplicate[6],
                    version_before=duplicate[7],
                    version_after=duplicate[8],
                    active_reserved_after=duplicate[9],
                    available_after=duplicate[10],
                )

            amount, version = capacity_row
            if expected_version != version:
                raise ReservationLedgerError(
                    "ACCOUNT_VERSION_CONFLICT",
                    "Account version güncel değil; retry gerekir.",
                )
            active_total = bounded(
                sum(
                    (positive(row[0]) for row in self.db.execute(
                        "SELECT amount FROM account_reservations WHERE account_id=? AND asset=? AND status='ACTIVE'",
                        (reservation.owner.account_id, reservation.asset),
                    ).fetchall()),
                    Q(0),
                )
            )
            available = bounded(positive(amount) - active_total)
            requested = positive(reservation.amount)
            if available < 0 or requested > available:
                raise ReservationLedgerError(
                    "ACCOUNT_CAPACITY_CONFLICT",
                    "Yeni reservation account kapasitesini aşar.",
                )
            active_after = bounded(active_total + requested)
            available_after = bounded(available - requested)
            version_after = version + 1
            commit = ReservationCommit(
                reservation_id=reservation.reservation_id,
                account_id=reservation.owner.account_id,
                asset=reservation.asset,
                amount=exact_text(requested),
                version_before=version,
                version_after=version_after,
                active_reserved_after=exact_text(active_after),
                available_after=exact_text(available_after),
            )
            self.db.execute(
                "INSERT INTO account_reservations(" 
                "reservation_id, account_id, product_id, position_mode, deal_id, allocation_id, asset, amount, "
                "status, version_before, version_after, active_reserved_after, available_after) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?)",
                (
                    commit.reservation_id,
                    reservation.owner.account_id,
                    reservation.owner.product_id,
                    reservation.owner.position_mode,
                    reservation.owner.deal_id,
                    reservation.owner.allocation_id,
                    reservation.asset,
                    commit.amount,
                    commit.version_before,
                    commit.version_after,
                    commit.active_reserved_after,
                    commit.available_after,
                ),
            )
            changed = self.db.execute(
                "UPDATE account_capacities SET version=? WHERE account_id=? AND asset=? AND version=?",
                (version_after, reservation.owner.account_id, reservation.asset, version),
            ).rowcount
            if changed != 1:
                raise ReservationLedgerError(
                    "ACCOUNT_VERSION_CONFLICT", "Account version atomik olarak değişmedi."
                )
            self.db.execute("COMMIT")
            return commit
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _initialize(self) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(f"PRAGMA application_id={LEDGER_APPLICATION_ID}")
            self.db.execute(f"PRAGMA user_version={LEDGER_SCHEMA_VERSION}")
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS account_capacities(" 
                "account_id TEXT NOT NULL, asset TEXT NOT NULL, amount TEXT NOT NULL, version INTEGER NOT NULL, "
                "PRIMARY KEY(account_id, asset))"
            )
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS account_reservations(" 
                "reservation_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, product_id TEXT NOT NULL, "
                "position_mode TEXT NOT NULL, deal_id TEXT NOT NULL, allocation_id TEXT, asset TEXT NOT NULL, "
                "amount TEXT NOT NULL, status TEXT NOT NULL CHECK(status='ACTIVE'), version_before INTEGER NOT NULL, "
                "version_after INTEGER NOT NULL, active_reserved_after TEXT NOT NULL, available_after TEXT NOT NULL)"
            )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _validate_existing(self) -> None:
        application_id = self.db.execute("PRAGMA application_id").fetchone()[0]
        schema_version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if application_id != LEDGER_APPLICATION_ID or schema_version != LEDGER_SCHEMA_VERSION:
            raise ReservationLedgerError(
                "ACCOUNT_LEDGER_UNSUPPORTED", "Reservation ledger şeması desteklenmiyor."
            )
        try:
            self.db.execute("SELECT 1 FROM account_capacities LIMIT 1")
            self.db.execute("SELECT 1 FROM account_reservations LIMIT 1")
        except sqlite3.Error as exc:
            raise ReservationLedgerError(
                "ACCOUNT_LEDGER_UNSUPPORTED", "Reservation ledger tabloları eksik."
            ) from exc

    def _close_after_open_failure(self) -> None:
        if hasattr(self, "db"):
            self.db.close()


def _same_reservation(reservation: AccountReservation, row: tuple[object, ...]) -> bool:
    return (
        reservation.owner.account_id,
        reservation.owner.product_id,
        reservation.owner.position_mode,
        reservation.owner.deal_id,
        reservation.owner.allocation_id,
        reservation.asset,
        reservation.amount,
    ) == row[:7]


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ReservationLedgerError(code, "Kimlik geçersiz.")


def _validate_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or _is_linked(candidate) or _is_linked(resolved.parent):
        raise ReservationLedgerError(
            "ACCOUNT_LEDGER_PATH_INVALID", "Reservation ledger linked/backup path üzerinde olamaz."
        )
    if not resolved.parent.is_dir() or (candidate.exists() and not candidate.is_file()):
        raise ReservationLedgerError(
            "ACCOUNT_LEDGER_PATH_INVALID", "Reservation ledger yolu geçersiz."
        )
    return candidate


def _is_linked(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())
