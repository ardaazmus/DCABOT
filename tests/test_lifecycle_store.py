import tempfile
import unittest
from pathlib import Path
import json

from check_workspace import ROOT
from dcabot.application.config_revision import new_config_revision
from dcabot.application.deal_lifecycle import DealLifecycleError, new_deal_lifecycle
from dcabot.application.lifecycle_event_contract import (
    LifecycleEventContractError,
    new_lifecycle_event,
)
from dcabot.persistence.lifecycle_store import LifecycleStore, LifecycleStoreError


def event(event_id: str, event_type: str, sequence: int):
    return new_lifecycle_event(
        event_id, "deal-1", "config-revision-1", event_type, sequence
    )


def revision():
    return new_config_revision(
        "config-revision-1",
        json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8")),
    )


class LifecycleStoreTests(unittest.TestCase):
    def test_restart_replays_the_same_lifecycle_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lifecycle.sqlite3"
            with LifecycleStore.create(path) as store:
                self.assertEqual(
                    store.append(event("event-1", "START", 1), config_revision=revision()),
                    "ACCEPTED",
                )
                self.assertEqual(
                    store.append(event("event-2", "PAUSE", 2), config_revision=revision()),
                    "ACCEPTED",
                )
                before = store.load()

            with LifecycleStore.open(path) as reopened:
                self.assertEqual(reopened.load(), before)

            self.assertEqual(before.lifecycle.status, "PAUSED")
            self.assertEqual(before.history, (event("event-1", "START", 1), event("event-2", "PAUSE", 2)))

    def test_exact_duplicate_is_persistent_idempotent_and_conflict_is_not_appended(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lifecycle.sqlite3"
            with LifecycleStore.create(path) as store:
                first = event("event-1", "START", 1)
                store.append(first, config_revision=revision())
                self.assertEqual(
                    store.append(first, config_revision=revision()), "DUPLICATE"
                )
                with self.assertRaisesRegex(
                    LifecycleEventContractError, "LIFECYCLE_EVENT_CONFLICT"
                ):
                    store.append(
                        event("event-1", "FAIL", 1), config_revision=revision()
                    )
                self.assertEqual(store.load().history, (first,))

    def test_invalid_transition_and_tampered_record_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lifecycle.sqlite3"
            with LifecycleStore.create(path) as store:
                with self.assertRaisesRegex(
                    DealLifecycleError, "LIFECYCLE_TRANSITION_INVALID"
                ):
                    store.append(
                        event("event-1", "RESUME", 1), config_revision=revision()
                    )
                self.assertEqual(store.load().history, ())
                store.append(event("event-1", "START", 1), config_revision=revision())
                store.db.execute(
                    "UPDATE lifecycle_events SET event_type='FAIL' WHERE event_id='event-1'"
                )
                with self.assertRaisesRegex(
                    LifecycleStoreError, "LIFECYCLE_RECORD_CORRUPT"
                ):
                    store.load()

    def test_revision_identity_is_bound_to_one_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lifecycle.sqlite3"
            raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
            changed = dict(raw)
            changed["target_quote"] = "2"
            original = new_config_revision("config-revision-1", raw)
            conflicting = new_config_revision("config-revision-1", changed)
            with LifecycleStore.create(path) as store:
                first = event("event-1", "START", 1)
                store.append(first, config_revision=original)
                with self.assertRaisesRegex(
                    LifecycleEventContractError, "CONFIG_REVISION_CONFLICT"
                ):
                    store.append(
                        event("event-2", "PAUSE", 2),
                        config_revision=conflicting,
                    )
                self.assertEqual(store.load().history, (first,))

                with self.assertRaisesRegex(
                    LifecycleEventContractError, "LIFECYCLE_EVENT_REVISION_CONFLICT"
                ):
                    store.append(
                        new_lifecycle_event(
                            "event-2", "deal-1", "config-revision-2", "PAUSE", 2
                        ),
                        config_revision=original,
                    )


if __name__ == "__main__":
    unittest.main()
