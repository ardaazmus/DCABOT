import unittest

from dcabot.application.shared_account_identity import (
    SharedAccountIdentity,
    SharedAccountIdentityError,
    new_shared_account_identity,
)


class SharedAccountIdentityTests(unittest.TestCase):
    def test_identity_preserves_explicit_account_product_mode_and_owner_scope(self):
        result = new_shared_account_identity(
            account_id="account-1",
            product_id="BTCUSDT",
            position_mode="SPOT",
            deal_id="deal-1",
            allocation_id="allocation-1",
        )

        self.assertEqual(
            result,
            SharedAccountIdentity(
                account_id="account-1",
                product_id="BTCUSDT",
                position_mode="SPOT",
                deal_id="deal-1",
                allocation_id="allocation-1",
            ),
        )

    def test_all_identity_components_are_scope_significant(self):
        base = new_shared_account_identity(
            account_id="account-1",
            product_id="BTCUSDT",
            position_mode="SPOT",
            deal_id="deal-1",
            allocation_id=None,
        )

        variants = (
            new_shared_account_identity("account-2", "BTCUSDT", "SPOT", "deal-1", None),
            new_shared_account_identity("account-1", "ETHUSDT", "SPOT", "deal-1", None),
            new_shared_account_identity("account-1", "BTCUSDT", "MODE-2", "deal-1", None),
            new_shared_account_identity("account-1", "BTCUSDT", "SPOT", "deal-2", None),
            new_shared_account_identity("account-1", "BTCUSDT", "SPOT", "deal-1", "allocation-1"),
        )

        self.assertTrue(all(variant != base for variant in variants))

    def test_invalid_required_or_optional_identity_fails_closed(self):
        with self.assertRaisesRegex(
            SharedAccountIdentityError, "SHARED_ACCOUNT_IDENTITY_INVALID"
        ):
            new_shared_account_identity("bad id", "BTCUSDT", "SPOT", "deal-1", None)

        with self.assertRaisesRegex(
            SharedAccountIdentityError, "SHARED_ACCOUNT_ALLOCATION_INVALID"
        ):
            new_shared_account_identity("account-1", "BTCUSDT", "SPOT", "deal-1", "bad id")


if __name__ == "__main__":
    unittest.main()
