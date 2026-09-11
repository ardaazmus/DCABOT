import unittest
from dataclasses import dataclass

from dcabot.application.read_only_explanations import (
    explain_historical_result,
    explain_public_replay,
)


@dataclass(frozen=True)
class Action:
    bar_index: int
    role: str


@dataclass(frozen=True)
class HistoricalResult:
    execution_status: str
    application_code: str | None
    position_status: str
    funding_status: str
    mark_status: str
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class ReplayResult:
    outcomes: tuple[object, ...]


class ReadOnlyExplanationTests(unittest.TestCase):
    def test_completed_result_explains_existing_authority_without_economic_fields(self):
        result = HistoricalResult(
            execution_status="COMPLETED",
            application_code=None,
            position_status="OPEN_AT_END",
            funding_status="NOT_MODELED",
            mark_status="NOT_AVAILABLE",
            actions=(Action(bar_index=1, role="BASE"),),
        )

        explanations = explain_historical_result(result)

        self.assertEqual(
            [(item.code, item.source) for item in explanations],
            [
                ("HISTORICAL_COMPLETED", "execution_status"),
                ("ACTION_RECORDED", "actions[0]"),
                ("POSITION_OPEN_AT_END", "position_status"),
                ("FUNDING_NOT_MODELED", "funding_status"),
                ("MARK_NOT_AVAILABLE", "mark_status"),
            ],
        )
        self.assertEqual(explanations[1].context, {"bar_index": 1, "role": "BASE"})
        self.assertNotIn("pnl", explanations[0].context)
        self.assertNotIn("fee", explanations[0].context)

    def test_indeterminate_result_does_not_claim_a_final_result(self):
        result = HistoricalResult(
            execution_status="INDETERMINATE",
            application_code="AMBIGUOUS_OHLC_PATH",
            position_status="OPEN_AT_END",
            funding_status="NOT_MODELED",
            mark_status="NOT_AVAILABLE",
            actions=(),
        )

        explanations = explain_historical_result(result)

        self.assertEqual(
            [item.code for item in explanations[:3]],
            [
                "HISTORICAL_INDETERMINATE",
                "AMBIGUOUS_OHLC_PATH",
                "POSITION_OPEN_AT_END",
            ],
        )
        self.assertIn("final", explanations[0].message)

    def test_public_replay_outcomes_are_explained_without_live_or_economic_claims(self):
        class Outcome:
            def __init__(self, value: str):
                self.value = value

        replay = ReplayResult(
            outcomes=(
                Outcome("ACCEPTED"),
                Outcome("DUPLICATE"),
                Outcome("SEQUENCE_GAP"),
            )
        )

        explanations = explain_public_replay(replay)

        self.assertEqual(
            [(item.code, item.source) for item in explanations],
            [
                ("OBSERVATION_ACCEPTED", "outcomes[0]"),
                ("OBSERVATION_DUPLICATE", "outcomes[1]"),
                ("OBSERVATION_SEQUENCE_GAP", "outcomes[2]"),
            ],
        )
        self.assertEqual(explanations[2].context, {"outcome_index": 2})
        for item in explanations:
            self.assertNotIn("order_id", item.context)
            self.assertNotIn("fill_id", item.context)

    def test_unknown_public_outcome_is_fail_closed(self):
        class Outcome:
            value = "UNEXPECTED"

        with self.assertRaises(ValueError):
            explain_public_replay(ReplayResult(outcomes=(Outcome(),)))


if __name__ == "__main__":
    unittest.main()
