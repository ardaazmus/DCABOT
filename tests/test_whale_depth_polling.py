"""Faz 17 E.3: depth REST snapshot çağrıları E.1'in Lab rate bütçesine
bağlanır -- ağırlık reddedilirse ağa hiç dokunulmaz; venue'nin kendi
used-weight header'ı varsa bütçenin gözlem tabanına beslenir."""
import json
import unittest

from dcabot.application.lab_rate_budget import LabRateBudget
from dcabot.application.whale_depth_polling import (
    WhaleDepthPollingError,
    fetch_depth_snapshot_within_budget,
)


class FakeResponse:
    status = 200

    def __init__(self, payload, *, used_weight_1m=None):
        body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Length": str(len(body))}
        if used_weight_1m is not None:
            self.headers["X-MBX-USED-WEIGHT-1M"] = str(used_weight_1m)
        self._body = body

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def close(self) -> None:
        pass


class FakeOpener:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = 0

    def open(self, request, timeout: int):
        self.calls += 1
        return self.response


PAYLOAD = {"lastUpdateId": 1, "bids": [], "asks": []}


class FetchDepthSnapshotWithinBudgetTests(unittest.TestCase):
    def test_allowed_call_fetches_and_feeds_observed_weight_back(self):
        budget = LabRateBudget(ceiling_weight_1m=100)
        opener = FakeOpener(FakeResponse(PAYLOAD, used_weight_1m=55))
        snapshot = fetch_depth_snapshot_within_budget(
            "BTCUSDT", limit=100, budget=budget, weight=5, now_us=1_000_000, opener=opener
        )
        self.assertEqual(opener.calls, 1)
        self.assertEqual(snapshot.last_update_id, 1)
        self.assertEqual(budget.usage_1m(now_us=1_000_000), 55)

    def test_denied_budget_never_touches_the_network(self):
        budget = LabRateBudget(ceiling_weight_1m=10)
        budget.allow("other-feature", 10, now_us=1_000_000)  # exhausts the ceiling
        opener = FakeOpener(FakeResponse(PAYLOAD))
        with self.assertRaises(WhaleDepthPollingError) as ctx:
            fetch_depth_snapshot_within_budget(
                "BTCUSDT", limit=100, budget=budget, weight=5, now_us=1_000_000, opener=opener
            )
        self.assertEqual(ctx.exception.code, "WHALE_DEPTH_BUDGET_DENIED")
        self.assertEqual(opener.calls, 0)

    def test_missing_weight_header_does_not_touch_the_budget_floor(self):
        budget = LabRateBudget(ceiling_weight_1m=100)
        opener = FakeOpener(FakeResponse(PAYLOAD))
        fetch_depth_snapshot_within_budget(
            "BTCUSDT", limit=100, budget=budget, weight=5, now_us=1_000_000, opener=opener
        )
        # Only the locally-recorded spend (5) counts, no venue floor was reported.
        self.assertEqual(budget.usage_1m(now_us=1_000_000), 5)


if __name__ == "__main__":
    unittest.main()
