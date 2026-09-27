"""Faz 17 E.3: resmi spot @depth U/u senkronizasyon durum makinesi
(REST lastUpdateId + WS diff-depth events -- spot'ta "pu" alanı YOK,
bkz. binance_public_depth.py docstring'i). Fake frame dizileriyle test
edilir, gerçek WS gerekmez."""
import unittest

from dcabot.application.whale_depth_sync import DepthBookSync, WhaleDepthSyncError
from dcabot.data_adapters.binance_public_depth import DepthDiffEvent, DepthSnapshot


def _snapshot(last_update_id, bids=(), asks=()):
    return DepthSnapshot(last_update_id=last_update_id, bids=bids, asks=asks, used_weight_1m=None)


def _event(u_first, u_final, bids=(), asks=(), *, symbol="BTCUSDT", event_time_ms=1):
    return DepthDiffEvent(
        symbol=symbol,
        event_time_ms=event_time_ms,
        first_update_id=u_first,
        final_update_id=u_final,
        bids=bids,
        asks=asks,
    )


class DepthBookSyncTests(unittest.TestCase):
    def test_events_before_snapshot_are_buffered_not_applied(self):
        sync = DepthBookSync()
        sync.apply_event(_event(1, 5))
        self.assertEqual(sync.state, "SYNCING")

    def test_first_event_covering_snapshot_id_reaches_in_sync(self):
        sync = DepthBookSync()
        sync.apply_snapshot(_snapshot(150, bids=(("4.0", "10"),)))
        state = sync.apply_event(_event(151, 160, bids=(("4.0", "9"),)))
        self.assertEqual(state, "IN_SYNC")
        self.assertEqual(sync.bids["4.0"], "9")

    def test_buffered_events_replay_in_order_on_snapshot_arrival(self):
        sync = DepthBookSync()
        sync.apply_event(_event(140, 145))  # stale, will be discarded (u<=150)
        sync.apply_event(_event(151, 160, bids=(("4.0", "5"),)))  # valid first
        state = sync.apply_snapshot(_snapshot(150, bids=(("4.0", "10"),)))
        self.assertEqual(state, "IN_SYNC")
        self.assertEqual(sync.bids["4.0"], "5")

    def test_stale_event_before_snapshot_id_is_ignored(self):
        sync = DepthBookSync()
        sync.apply_snapshot(_snapshot(150))
        state = sync.apply_event(_event(100, 150))  # u == lastUpdateId, stale
        self.assertEqual(state, "SYNCING")  # still waiting for the real first event

    def test_gap_on_first_event_is_detected(self):
        sync = DepthBookSync()
        sync.apply_snapshot(_snapshot(150))
        # U(152) > lastUpdateId+1(151) -- missed the bridging event.
        state = sync.apply_event(_event(152, 160))
        self.assertEqual(state, "GAP_DETECTED")

    def test_gap_while_in_sync_is_detected(self):
        sync = DepthBookSync()
        sync.apply_snapshot(_snapshot(150))
        sync.apply_event(_event(151, 160))
        state = sync.apply_event(_event(165, 170))  # 165 > 160+1
        self.assertEqual(state, "GAP_DETECTED")

    def test_contiguous_events_stay_in_sync_and_merge_levels(self):
        sync = DepthBookSync()
        sync.apply_snapshot(_snapshot(150, bids=(("4.0", "10"),)))
        sync.apply_event(_event(151, 160, bids=(("4.0", "9"),)))
        state = sync.apply_event(_event(161, 165, bids=(("4.1", "3"),)))
        self.assertEqual(state, "IN_SYNC")
        self.assertEqual(sync.bids["4.0"], "9")
        self.assertEqual(sync.bids["4.1"], "3")

    def test_zero_quantity_removes_the_level(self):
        sync = DepthBookSync()
        sync.apply_snapshot(_snapshot(150, bids=(("4.0", "10"),)))
        sync.apply_event(_event(151, 160, bids=(("4.0", "0"),)))
        self.assertNotIn("4.0", sync.bids)

    def test_resync_after_gap_clears_and_restarts(self):
        sync = DepthBookSync()
        sync.apply_snapshot(_snapshot(150, bids=(("4.0", "10"),)))
        sync.apply_event(_event(151, 160))
        sync.apply_event(_event(165, 170))  # gap
        self.assertEqual(sync.state, "GAP_DETECTED")
        state = sync.apply_snapshot(_snapshot(200, bids=(("5.0", "1"),)))
        self.assertEqual(state, "SYNCING")
        state = sync.apply_event(_event(201, 205, bids=(("5.0", "2"),)))
        self.assertEqual(state, "IN_SYNC")
        self.assertNotIn("4.0", sync.bids)
        self.assertEqual(sync.bids["5.0"], "2")

    def test_event_for_a_different_symbol_is_rejected(self):
        sync = DepthBookSync(symbol="BTCUSDT")
        sync.apply_snapshot(_snapshot(150))
        with self.assertRaises(WhaleDepthSyncError):
            sync.apply_event(_event(151, 160, symbol="ETHUSDT"))


if __name__ == "__main__":
    unittest.main()
