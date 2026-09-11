"""Versioned SQLite offline journal. Batches, economics and postings commit together."""

import hashlib
import json
import sqlite3
from pathlib import Path
from fractions import Fraction as Q
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply, identifier
from dcabot.domain.numbers import ratio

APP_ID = 0x44434142
SCHEMA = 1
ENGINE = "offline-core-1"


def canonical(value) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, path: Path, config: dict | None = None):
        path = Path(path)
        if "YEDEK_ESKI_PROJE" in path.resolve().parts or any(
            p.is_symlink() or p.is_junction() for p in (path, *path.parents)
        ):
            raise ValueError("Database must not use backup or linked paths")
        if config is not None:
            Config.parse(config)
            # Exclusive create: never open or migrate a pre-existing user database.
            with path.open("xb"):
                pass
        elif not path.is_file():
            raise ValueError("Database missing: use init explicitly")
        self.db = sqlite3.connect(
            path.resolve().as_uri() + "?mode=rw",
            uri=True,
            isolation_level=None,
            timeout=5,
        )
        try:
            if config is not None:
                self.db.executescript(f"""
                    BEGIN IMMEDIATE;
                    PRAGMA application_id={APP_ID};
                    PRAGMA user_version={SCHEMA};
                    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                    CREATE TABLE batches(id TEXT PRIMARY KEY,request TEXT NOT NULL);
                    CREATE TABLE events(seq INTEGER PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES batches(id),
                        payload TEXT NOT NULL,hash TEXT NOT NULL,execution_id TEXT UNIQUE);
                    CREATE TABLE postings(event_seq INTEGER NOT NULL REFERENCES events(seq), account TEXT NOT NULL,
                        numerator TEXT NOT NULL,denominator TEXT NOT NULL, PRIMARY KEY(event_seq,account));
                    CREATE TABLE incidents(seq INTEGER PRIMARY KEY,batch_id TEXT NOT NULL,request TEXT NOT NULL,reason TEXT NOT NULL);
                    COMMIT;
                """)
                with self.db:
                    for key, value in [
                        ("engine", ENGINE),
                        ("config", canonical(config)),
                        ("config_hash", digest(canonical(config))),
                    ]:
                        self.db.execute(
                            "INSERT INTO metadata VALUES (?,?)", (key, value)
                        )
            if (
                self.db.execute("PRAGMA application_id").fetchone()[0] != APP_ID
                or self.db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA
            ):
                raise ValueError("Not a supported DCABOT offline database")
            meta = dict(self.db.execute("SELECT key,value FROM metadata"))
            if meta.get("engine") != ENGINE or digest(meta["config"]) != meta.get(
                "config_hash"
            ):
                raise ValueError("Engine/config metadata mismatch")
            self.raw_config = json.loads(meta["config"])
            self.config = Config.parse(self.raw_config)
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.audit()
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _load(self) -> State:
        state = State(peak=self.config.initial_equity)
        for payload, checksum in self.db.execute(
            "SELECT payload,hash FROM events ORDER BY seq"
        ):
            if digest(payload) != checksum:
                raise Conflict("Stored event hash mismatch")
            state = apply(state, json.loads(payload), self.config)
        if self.db.execute("SELECT 1 FROM incidents LIMIT 1").fetchone():
            state.blockers.append("PERSISTENT_INCIDENT_REQUIRES_REVIEW")
        return state

    def load(self) -> State:
        self.db.execute("BEGIN")
        try:
            result = self._load()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _write(self, batch_id: str, event: dict, state: State) -> tuple[State, bool]:
        payload = canonical(event)
        execution = event.get("execution_id") if event.get("type") == "FILL" else None
        if execution is not None:
            identifier(execution)
            prior = self.db.execute(
                "SELECT payload FROM events WHERE execution_id=?", (execution,)
            ).fetchone()
            if prior:
                if prior[0] != payload:
                    raise Conflict("Same execution ID with different economic payload")
                return state, False
        after = apply(state, event, self.config)
        seq = self.db.execute(
            "INSERT INTO events(batch_id,payload,hash,execution_id) VALUES (?,?,?,?)",
            (batch_id, payload, digest(payload), execution),
        ).lastrowid
        gross = after.realized - state.realized
        fee = after.fees - state.fees
        funding = after.funding - state.funding
        entries = {
            "WALLET": gross - fee - funding,
            "REALIZED_PNL": -gross,
            "FEE_EXPENSE": fee,
            "FUNDING_EXPENSE": funding,
        }
        assert sum(entries.values()) == 0
        for account, amount in entries.items():
            if amount:
                numerator, denominator = ratio(amount)
                self.db.execute(
                    "INSERT INTO postings VALUES (?,?,?,?)",
                    (seq, account, numerator, denominator),
                )
        return after, True

    def transact(self, batch_id: str, request: dict, builder) -> bool:
        """builder(state, emit) runs inside a local transaction; never perform I/O there."""
        identifier(batch_id)
        payload = canonical(request)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior = self.db.execute(
                "SELECT request FROM batches WHERE id=?", (batch_id,)
            ).fetchone()
            if prior:
                if prior[0] != payload:
                    raise Conflict("Same batch ID with different request")
                self.db.execute("COMMIT")
                return False
            if self.db.execute("SELECT count(*) FROM events").fetchone()[0] >= 10000:
                raise ValueError("Offline journal limit is 10000 events")
            state = self._load()
            self.db.execute("INSERT INTO batches VALUES (?,?)", (batch_id, payload))

            def emit(event):
                nonlocal state
                state, _ = self._write(batch_id, event, state)
                return state

            builder(state, emit)
            if self.db.execute("SELECT count(*) FROM events").fetchone()[0] > 10000:
                raise ValueError("Offline journal limit is 10000 events")
            self.db.execute("COMMIT")
            return True
        except BaseException as exc:
            self.db.execute("ROLLBACK")
            # Preserve conflicting/invalid synthetic executions without silently accepting them.
            quarantine = isinstance(exc, Conflict) or (
                isinstance(exc, ValueError)
                and request.get("type") in ("FILL", "ORDER_FINAL")
            )
            if quarantine:
                self.db.execute("BEGIN IMMEDIATE")
                try:
                    self.db.execute(
                        "INSERT INTO incidents(batch_id,request,reason) VALUES (?,?,?)",
                        (batch_id, payload, str(exc)),
                    )
                    self.db.execute("COMMIT")
                except BaseException:
                    self.db.execute("ROLLBACK")
                    raise
            raise

    def append(self, event_id: str, event: dict) -> bool:
        return self.transact(event_id, event, lambda _state, emit: emit(event))

    def audit(self) -> dict:
        self.db.execute("BEGIN")
        try:
            state = self._load()
            totals = {}
            by_event = {}
            for seq, account, n, d in self.db.execute(
                "SELECT event_seq,account,numerator,denominator FROM postings"
            ):
                value = Q(int(n), int(d))
                totals[account] = totals.get(account, Q(0)) + value
                by_event[seq] = by_event.get(seq, Q(0)) + value
            if (
                any(by_event.values())
                or totals.get("WALLET", Q(0))
                != state.realized - state.fees - state.funding
            ):
                raise Conflict("Posting ledger does not reconcile to economic events")
            # Recompute each posting, not merely the grand total (which can hide offsetting errors).
            previous = State(peak=self.config.initial_equity)
            for seq, payload in self.db.execute(
                "SELECT seq,payload FROM events ORDER BY seq"
            ):
                after = apply(previous, json.loads(payload), self.config)
                g = after.realized - previous.realized
                f = after.fees - previous.fees
                u = after.funding - previous.funding
                expected = {
                    k: v
                    for k, v in {
                        "WALLET": g - f - u,
                        "REALIZED_PNL": -g,
                        "FEE_EXPENSE": f,
                        "FUNDING_EXPENSE": u,
                    }.items()
                    if v
                }
                actual = {
                    a: Q(int(n), int(d))
                    for a, n, d in self.db.execute(
                        "SELECT account,numerator,denominator FROM postings WHERE event_seq=?",
                        (seq,),
                    )
                }
                if actual != expected:
                    raise Conflict("Per-event posting mismatch")
                previous = after
            if (
                self.db.execute("PRAGMA foreign_key_check").fetchone()
                or self.db.execute("PRAGMA quick_check").fetchone()[0] != "ok"
            ):
                raise Conflict("SQLite integrity check failed")
            result = {
                "status": "PASS",
                "events": self.db.execute("SELECT count(*) FROM events").fetchone()[0],
                "incidents": self.db.execute(
                    "SELECT count(*) FROM incidents"
                ).fetchone()[0],
                "scope": "OFFLINE_JOURNAL_AND_BALANCED_CASH_POSTINGS",
            }
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
