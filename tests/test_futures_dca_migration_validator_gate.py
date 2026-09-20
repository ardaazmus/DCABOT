from dataclasses import dataclass
import hashlib
import unittest


@dataclass(frozen=True, slots=True)
class DraftMigrationRow:
    event_id: str
    sequence_no: int
    profile_revision_id: str
    reservation_id: str
    posting_cursor: int
    payload_hash: str
    state: str


def validate_draft_migration(rows: tuple[DraftMigrationRow, ...]) -> tuple[DraftMigrationRow, ...]:
    if not rows:
        raise ValueError("empty migration")
    profile_revision_id = rows[0].profile_revision_id
    seen: set[str] = set()
    for expected_sequence, row in enumerate(rows, start=1):
        if row.sequence_no != expected_sequence:
            raise ValueError("sequence gap")
        if not row.profile_revision_id or row.profile_revision_id != profile_revision_id:
            raise ValueError("profile conflict")
        if not row.event_id or row.event_id in seen:
            raise ValueError("event identity conflict")
        if not row.reservation_id or row.posting_cursor < 0:
            raise ValueError("binding identity missing")
        expected_hash = hashlib.sha256(row.event_id.encode("utf-8")).hexdigest()
        if row.payload_hash != expected_hash:
            raise ValueError("checksum invalid")
        if row.state != "ACCEPTED":
            raise ValueError("non-replayable state")
        seen.add(row.event_id)
    return rows


def row(sequence_no: int, *, state: str = "ACCEPTED", profile_revision_id: str = "profile-1") -> DraftMigrationRow:
    payload_hash = hashlib.sha256(f"event-{sequence_no}".encode("utf-8")).hexdigest()
    return DraftMigrationRow(
        event_id=f"event-{sequence_no}",
        sequence_no=sequence_no,
        profile_revision_id=profile_revision_id,
        reservation_id=f"reservation-{sequence_no}",
        posting_cursor=sequence_no,
        payload_hash=payload_hash,
        state=state,
    )


class FuturesDcaMigrationValidatorGateTests(unittest.TestCase):
    def test_valid_rows_replay_in_the_same_order(self):
        rows = (row(1), row(2))

        validated = validate_draft_migration(rows)

        self.assertEqual(validated, rows)

    def test_profile_sequence_identity_and_checksum_conflicts_fail_closed(self):
        cases = (
            (row(1), row(3)),
            (row(1), row(2, profile_revision_id="profile-2")),
            (row(1), DraftMigrationRow("event-1", 2, "profile-1", "reservation-1", 1, row(1).payload_hash, "ACCEPTED")),
            (DraftMigrationRow("event-1", 1, "profile-1", "reservation-1", 1, "0" * 64, "ACCEPTED"),),
        )

        for candidate in cases:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                validate_draft_migration(candidate)

    def test_unknown_or_quarantined_rows_cannot_be_migrated_as_economic_state(self):
        with self.assertRaisesRegex(ValueError, "non-replayable state"):
            validate_draft_migration((row(1, state="UNKNOWN"),))


if __name__ == "__main__":
    unittest.main()
