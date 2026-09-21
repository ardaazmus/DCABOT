"""F10.9: chart draft-level validation core (F29)."""
import unittest

from dcabot.application.draft_level import DraftLevelError, validate_draft_level


class DraftLevelTests(unittest.TestCase):
    def test_inside_range_accepted(self):
        result = validate_draft_level(low="90", high="110", draft_price="105.5")
        self.assertEqual(result["verdict"], "ACCEPTED")
        self.assertEqual(result["draft_price"], "105.5")

    def test_boundary_accepted(self):
        for price in ("90", "110"):
            with self.subTest(price=price):
                result = validate_draft_level(low="90", high="110", draft_price=price)
                self.assertEqual(result["verdict"], "ACCEPTED")

    def test_outside_range_rejected(self):
        for price in ("89.999", "110.001"):
            with self.subTest(price=price):
                result = validate_draft_level(low="90", high="110", draft_price=price)
                self.assertEqual(result["verdict"], "REJECTED")
                self.assertTrue(result["reason"])

    def test_non_numeric_rejected(self):
        with self.assertRaises(DraftLevelError) as ctx:
            validate_draft_level(low="90", high="110", draft_price="high")
        self.assertEqual(ctx.exception.code, "DRAFT_PRICE_INVALID")

    def test_inverted_range_rejected(self):
        with self.assertRaises(DraftLevelError):
            validate_draft_level(low="110", high="90", draft_price="100")


if __name__ == "__main__":
    unittest.main()
