import ast
import unittest
from pathlib import Path

from dcabot.data_adapters.binance_public import (
    BinanceTimeUnit,
    normalize_binance_rest_trade_payload,
    normalize_binance_trade_payload,
    replay_binance_observations,
)
from dcabot.data_adapters.public_feed import FeedState, ObservationOutcome, PublicObservation, ReplayResult


ALLOWLIST = frozenset({"BTCUSDT"})
RECEIVE_US = 1_700_000_000_000_100
PROCESSING_US = 1_700_000_000_000_200


def trade_payload(**overrides) -> dict:
    payload = {
        "e": "trade",
        "E": 1_700_000_000_001,
        "s": "BTCUSDT",
        "t": 5000,
        "p": "50000.00",
        "q": "0.01000000",
        "T": 1_700_000_000_000,
        "m": False,
    }
    payload.update(overrides)
    return payload


def rest_trade_payload(**overrides) -> dict:
    payload = {
        "id": 28457,
        "price": "50000.00",
        "qty": "0.01000000",
        "quoteQty": "500.00000000",
        "time": 1_700_000_000_000,
        "isBuyerMaker": True,
        "isBestMatch": True,
    }
    payload.update(overrides)
    return payload


def normalize_trade(payload: dict):
    return normalize_binance_trade_payload(
        payload,
        allowed_symbols=ALLOWLIST,
        receive_time_us=RECEIVE_US,
        processing_time_us=PROCESSING_US,
        time_unit=BinanceTimeUnit.MILLISECONDS,
    )


class BinanceCapabilityBoundaryTests(unittest.TestCase):
    def test_normalize_and_replay_expose_only_read_only_data_contracts(self):
        websocket_observation = normalize_trade(
            trade_payload(
                candidate_id="untrusted",
                order_id="untrusted",
                fill_id="untrusted",
                reserve="untrusted",
                balance="untrusted",
                pnl="untrusted",
            )
        )
        rest_observation = normalize_binance_rest_trade_payload(
            rest_trade_payload(),
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        replay = replay_binance_observations(
            (websocket_observation,),
            now_times_us=(PROCESSING_US,),
            max_staleness_us=1_000,
        )

        self.assertIsInstance(websocket_observation, PublicObservation)
        self.assertIsInstance(rest_observation, PublicObservation)
        self.assertIsInstance(replay, ReplayResult)
        self.assertEqual(replay.outcomes, (ObservationOutcome.ACCEPTED,))
        self.assertEqual(replay.cursor.state, FeedState.SYNCED)
        self.assertEqual(
            {field.name for field in PublicObservation.__dataclass_fields__.values()},
            {
                "source_id",
                "transport",
                "symbol",
                "product",
                "event_id",
                "event_time_us",
                "receive_time_us",
                "processing_time_us",
                "price",
                "quantity",
                "payload_hash",
                "source_sequence",
                "stream_type",
                "exchange_time_us",
                "is_buyer_maker",
                "buyer_order_id",
                "seller_order_id",
                "first_trade_id",
                "last_trade_id",
            },
        )
        for result in (
            websocket_observation,
            rest_observation,
            replay,
            *replay.cursor.accepted,
        ):
            for forbidden in ("candidate_id", "order_id", "fill_id", "reserve", "balance", "pnl"):
                self.assertFalse(hasattr(result, forbidden))
        self.assertFalse(hasattr(replay.cursor, "order"))
        self.assertFalse(hasattr(replay.cursor, "fill"))

    def test_binance_adapter_import_graph_has_no_network_or_economic_module(self):
        source_path = (
            Path(__file__).parents[1]
            / "src"
            / "dcabot"
            / "data_adapters"
            / "binance_public.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported_modules.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )

        self.assertTrue(
            imported_modules.issubset(
                {
                    "enum",
                    "hashlib",
                    "json",
                    "dcabot.data_adapters.public_feed",
                    "dcabot.domain.numbers",
                }
            )
        )
        self.assertFalse(
            imported_modules
            & {"socket", "ssl", "http", "urllib", "requests", "websockets", "dcabot.application", "dcabot.core"}
        )


if __name__ == "__main__":
    unittest.main()
