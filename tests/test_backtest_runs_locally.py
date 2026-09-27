"""Faz 17 J.1: backtest/sweep/optimize calls run locally and synchronously.

Acceptance proof (no architecture change): the three local compute entry
points complete while every network-opening primitive is blocked --
socket connect, DNS resolution, urllib opener/urlopen, plus
requests/httpx transports when those libraries are installed. Same
spirit as `test_denied_budget_never_touches_the_network` (whale depth
polling): instead of a fake injected port, the guard sits one layer
lower, at the primitives every HTTP client funnels through.

Scope note: `run_parameter_sweep` is exercised with `max_workers=1`
(the sequential, in-process path). The `max_workers>1` path spawns
local worker processes that cannot inherit an in-process monkeypatch;
those workers only unpickle a local bar cache and run the same
reducer (`run_sweep_task`), with no network imports on that path.
"""
import contextlib
import socket
import unittest
import urllib.request
from unittest import mock

from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.application.sweep_optimize import optimize_parameters
from dcabot.application.sweep_orchestrator import run_parameter_sweep
from dcabot.data_adapters.historical import (
    CanonicalBar,
    HistoricalDatasetInput,
    HistoricalDatasetMetadata,
)
from dcabot.domain.config import Config


class NetworkBlockedError(AssertionError):
    """Raised by the guard if production code attempts any network access."""


def _blocked(*args, **kwargs):
    raise NetworkBlockedError("network access is blocked in this test")


@contextlib.contextmanager
def block_network():
    """Block every socket-opening primitive for the duration of one call."""
    patches = [
        mock.patch.object(socket.socket, "connect", _blocked),
        mock.patch.object(socket.socket, "connect_ex", _blocked),
        mock.patch("socket.create_connection", _blocked),
        mock.patch("socket.getaddrinfo", _blocked),
        mock.patch("urllib.request.urlopen", _blocked),
        mock.patch("urllib.request.OpenerDirector.open", _blocked),
    ]
    try:
        import requests.adapters

        patches.append(mock.patch.object(requests.adapters.HTTPAdapter, "send", _blocked))
    except ImportError:
        pass
    try:
        import httpx

        patches.append(mock.patch.object(httpx.HTTPTransport, "handle_request", _blocked))
    except ImportError:
        pass
    with contextlib.ExitStack() as stack:
        for patcher in patches:
            stack.enter_context(patcher)
        yield


def _dataset() -> HistoricalDatasetInput:
    metadata = HistoricalDatasetMetadata(
        dataset_id="local-proof-fixture",
        source_id="fixture",
        symbol="BTCUSDT",
        interval="1h",
        period_start="2024-01-01",
        period_end="2024-01-02",
        artifact_sha256="f" * 64,
        artifact_bytes=64,
        timestamp_unit="microseconds",
        timezone="UTC",
    )
    bars = tuple(
        CanonicalBar(
            open_time_us=i * 3_600_000_000,
            close_time_us=(i + 1) * 3_600_000_000 - 1,
            open="100.00",
            high="101.00",
            low="99.00",
            close="100.50",
            base_volume="1",
            is_closed=True,
        )
        for i in range(4)
    )
    return HistoricalDatasetInput(metadata=metadata, bars=bars)


def _base_config() -> dict:
    return {
        "schema_version": 1,
        "mode": "offline",
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "base_qty": "0.001",
        "safety_qty": "0.002",
        "safety_count": 2,
        "deviation": "0.1",
        "step_multiplier": "1",
        "volume_multiplier": "1",
        "tick": "0.01",
        "qty_step": "0.001",
        "min_qty": "0.001",
        "min_notional": "0.01",
        "initial_equity": "1000",
        "max_entry_notional": "1000",
        "leverage": "1",
        "max_drawdown": "0.25",
        "minimum_equity": "100",
        "take_profit": "0.02",
        "target_mode": "GROSS_PRICE_RETURN",
        "target_quote": "5",
        "fee_rate": "0.001",
        "fee_quantum": "0.00000001",
        "slippage": "0",
        "margin_mode": "ISOLATED",
    }


class BacktestRunsLocallyTests(unittest.TestCase):
    def test_guard_blocks_socket_connect(self):
        with block_network():
            probe = socket.socket()
            try:
                with self.assertRaises(NetworkBlockedError):
                    probe.connect(("127.0.0.1", 1))
            finally:
                probe.close()
            with self.assertRaises(NetworkBlockedError):
                urllib.request.urlopen("http://127.0.0.1/")

    def test_backtest_run_completes_without_network(self):
        config = Config.parse(_base_config())
        with block_network():
            result = simulate_historical_ohlcv(
                _dataset(), config, config_hash="0" * 64
            )
        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertEqual(result.processed_bar_count, 4)

    def test_sequential_sweep_completes_without_network(self):
        recipes = (
            {"recipe_id": "r1", "overrides": {"take_profit": "0.02"}},
            {"recipe_id": "r2", "overrides": {"take_profit": "0.05"}},
        )
        with block_network():
            results = run_parameter_sweep(
                recipes, base_config=_base_config(), dataset=_dataset(), max_workers=1
            )
        self.assertEqual([r["recipe_id"] for r in results], ["r1", "r2"])
        for result in results:
            self.assertEqual(result["execution_status"], "COMPLETED")

    def test_optimize_completes_without_network(self):
        space = {"take_profit": {"kind": "categorical", "choices": ["0.02", "0.05"]}}
        with block_network():
            result = optimize_parameters(
                _dataset(),
                _base_config(),
                space=space,
                max_trials=2,
                seed=0,
                sampler="grid",
            )
        self.assertEqual(result["trial_count"], 2)
        self.assertIn("best_recipe_id", result)


if __name__ == "__main__":
    unittest.main()
