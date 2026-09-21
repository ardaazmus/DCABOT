"""Faz 12.3: Küme B yürütme projeksiyonları API'ye bağlanıyor (salt okunur)."""
import unittest

from dcabot.server.api import (
    _futures_grid_lifecycle,
    _futures_grid_margin,
    _futures_grid_placement,
    _futures_grid_policy,
    _futures_grid_position,
    _futures_grid_variants,
    _validate_futures_grid_lifecycle_payload,
    _validate_futures_grid_margin_payload,
    _validate_futures_grid_placement_payload,
    _validate_futures_grid_position_payload,
)


def _levels(**overrides):
    body = {
        "direction": "LONG",
        "level_mode": "ARITHMETIC",
        "lower_price": "100",
        "upper_price": "200",
        "interval_count": 2,
        "price_tick": "1",
        "tick_origin": "0",
    }
    body.update(overrides)
    return body


def _fills():
    return [
        {"fill_id": "f1", "side": "BUY", "price": "100", "quantity": "1", "effective_time_us": 1000},
        {"fill_id": "f2", "side": "BUY", "price": "150", "quantity": "1", "effective_time_us": 2000},
    ]


class FuturesGridPlacementApiTests(unittest.TestCase):
    def test_static_placement_exposes_candidates(self):
        validated, fields = _validate_futures_grid_placement_payload(
            {**_levels(), "placement_mode": "STATIC", "range_policy": "FIXED"}
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_placement(validated)
        self.assertEqual(result["decision"], "STATIC_CANDIDATE_ONLY")
        self.assertEqual(result["candidate_levels"], ["100", "150", "200"])
        self.assertEqual(result["order_authority"], "NONE")

    def test_dynamic_placement_stays_blocked(self):
        validated, fields = _validate_futures_grid_placement_payload(
            {**_levels(), "placement_mode": "DYNAMIC", "range_policy": "FIXED"}
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_placement(validated)
        self.assertEqual(result["decision"], "BLOCKED_CONTRACT_REQUIRED")

    def test_bad_mode_is_field_error(self):
        validated, fields = _validate_futures_grid_placement_payload(
            {**_levels(), "placement_mode": "AUTO", "range_policy": "FIXED"}
        )
        self.assertIsNone(validated)
        self.assertIn("placement_mode", fields)


class FuturesGridPositionApiTests(unittest.TestCase):
    def test_position_projects_quantity_and_average(self):
        validated, fields = _validate_futures_grid_position_payload(
            {"direction": "LONG", "fills": _fills()}
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_position(validated)
        self.assertEqual(result["position_side"], "LONG")
        self.assertEqual(result["quantity"], "2")
        self.assertEqual(result["average_entry"], "125")

    def test_empty_fills_is_field_error(self):
        validated, fields = _validate_futures_grid_position_payload(
            {"direction": "LONG", "fills": []}
        )
        self.assertIsNone(validated)
        self.assertIn("fills", fields)


class FuturesGridMarginApiTests(unittest.TestCase):
    def test_margin_projects_initial_requirement(self):
        validated, fields = _validate_futures_grid_margin_payload(
            {
                "direction": "LONG",
                "fills": _fills(),
                "reference_price": "150",
                "contract_size": "1",
                "available_margin": "1000",
            }
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_margin(validated)
        self.assertEqual(result["notional"], "300")
        self.assertEqual(result["required_initial_margin"], "300")
        self.assertEqual(result["capacity_status"], "ELIGIBLE")

    def test_short_margin_uses_same_path(self):
        validated, fields = _validate_futures_grid_margin_payload(
            {
                "direction": "SHORT",
                "fills": [
                    {"fill_id": "s1", "side": "SELL", "price": "200", "quantity": "1", "effective_time_us": 1000}
                ],
                "reference_price": "190",
                "contract_size": "2",
            }
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_margin(validated)
        self.assertEqual(result["notional"], "380")
        self.assertEqual(result["capacity_status"], "UNVERIFIED")


class FuturesGridLifecycleApiTests(unittest.TestCase):
    def test_fill_wins_and_late_cancel_quarantines(self):
        validated, fields = _validate_futures_grid_lifecycle_payload(
            {
                "events": [
                    {"event_id": "e1", "event_type": "FILL_ACCEPTED", "event_sequence": 1, "fill_id": "f1"},
                    {"event_id": "e2", "event_type": "CANCEL_REQUESTED", "event_sequence": 2},
                ]
            }
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_lifecycle(validated)
        self.assertEqual(result["status"], "QUARANTINED")
        self.assertEqual(result["fill_ids"], ["f1"])
        self.assertEqual(result["order_authority"], "NONE")

    def test_cancel_confirmed_replays_to_canceled(self):
        validated, fields = _validate_futures_grid_lifecycle_payload(
            {
                "events": [
                    {"event_id": "e1", "event_type": "CANCEL_REQUESTED", "event_sequence": 1},
                    {"event_id": "e2", "event_type": "CANCEL_CONFIRMED", "event_sequence": 2},
                ]
            }
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_lifecycle(validated)
        self.assertEqual(result["status"], "CANCELED")

    def test_unknown_observation_quarantines(self):
        validated, fields = _validate_futures_grid_lifecycle_payload(
            {"events": [{"event_id": "e9", "event_type": "UNKNOWN_OBSERVATION", "event_sequence": 1}]}
        )
        self.assertEqual(fields, {})
        assert validated is not None
        result = _futures_grid_lifecycle(validated)
        self.assertEqual(result["status"], "QUARANTINED")


class FuturesGridPolicyApiTests(unittest.TestCase):
    def test_policy_is_static_declaration(self):
        result = _futures_grid_policy()
        self.assertEqual(result["scope"], "DCABOT_OFFLINE_SIMULATION_ONLY")
        self.assertEqual(result["order_authority"], "NONE")

    def test_variants_stay_blocked_with_reason(self):
        result = _futures_grid_variants()
        by_variant = {row["variant"]: row for row in result["variants"]}
        self.assertEqual(by_variant["INFINITY_GRID"]["admission"], "BLOCKED")
        self.assertEqual(by_variant["REVERSE_GRID"]["admission"], "BLOCKED")
        self.assertEqual(by_variant["INFINITY_GRID"]["reason"], "FUTURES_GRID_VARIANT_NOT_VERIFIED")
