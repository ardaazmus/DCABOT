import json
import sys
import unittest
from uuid import uuid4

from dcabot.application.credential_boundary import (
    AccountCapability,
    CapabilitySource,
    CredentialMaterial,
    EphemeralCredentialProvider,
    credential_public_metadata,
)
from dcabot.application.signed_request import ApiKeyType, SignedRequestError
from dcabot.application.windows_credential_provider import WindowsCredentialManagerProvider


class CredentialBoundaryTests(unittest.TestCase):
    def test_ephemeral_provider_round_trip_never_exposes_material(self):
        material = CredentialMaterial(
            credential_id="test-credential",
            api_key="dummy-api-key",
            key_type=ApiKeyType.HMAC,
            secret=b"dummy-secret",
        )
        provider = EphemeralCredentialProvider()

        provider.put(material)
        loaded = provider.load("test-credential")

        self.assertEqual(loaded, material)
        self.assertNotIn("dummy-secret", repr(loaded))
        self.assertNotIn("dummy-api-key", json.dumps(credential_public_metadata(loaded)))

    def test_hmac_credential_requires_nonempty_bytes_material(self):
        with self.assertRaisesRegex(SignedRequestError, "CREDENTIAL_SECRET_INVALID"):
            CredentialMaterial(
                credential_id="test-credential",
                api_key="dummy-api-key",
                key_type=ApiKeyType.HMAC,
                secret=None,
            )

    def test_public_venue_metadata_cannot_become_account_trade_capability(self):
        with self.assertRaisesRegex(SignedRequestError, "ACCOUNT_CAPABILITY_SOURCE_INVALID"):
            AccountCapability.from_evidence(
                source=CapabilitySource.PUBLIC_VENUE_METADATA,
                signed_request_verified=False,
                can_trade=True,
                trade_scope_verified=True,
            )

    def test_direct_public_capability_construction_is_also_rejected(self):
        with self.assertRaisesRegex(SignedRequestError, "ACCOUNT_CAPABILITY_SOURCE_INVALID"):
            AccountCapability(
                source=CapabilitySource.PUBLIC_VENUE_METADATA,
                signed_request_verified=False,
                can_trade=True,
                trade_scope_verified=True,
            )

    def test_signed_account_capability_requires_verified_signed_request(self):
        with self.assertRaisesRegex(SignedRequestError, "ACCOUNT_SIGNATURE_UNVERIFIED"):
            AccountCapability.from_evidence(
                source=CapabilitySource.SIGNED_ACCOUNT_CONTEXT,
                signed_request_verified=False,
                can_trade=True,
                trade_scope_verified=True,
            )

    def test_signed_account_capability_is_explicit_and_has_no_secret_fields(self):
        capability = AccountCapability.from_evidence(
            source=CapabilitySource.SIGNED_ACCOUNT_CONTEXT,
            signed_request_verified=True,
            can_trade=True,
            trade_scope_verified=True,
        )

        self.assertEqual(
            capability,
            AccountCapability(
                source=CapabilitySource.SIGNED_ACCOUNT_CONTEXT,
                signed_request_verified=True,
                can_trade=True,
                trade_scope_verified=True,
            ),
        )
        self.assertNotIn("secret", capability.__dataclass_fields__)
        self.assertNotIn("api_key", capability.__dataclass_fields__)

    @unittest.skipUnless(sys.platform == "win32", "Windows Credential Manager yalnız Windows’ta çalışır.")
    def test_windows_provider_round_trip_is_redacted(self):
        credential_id = f"test-{uuid4().hex}"
        provider = WindowsCredentialManagerProvider()
        self.addCleanup(provider.delete, credential_id)
        material = CredentialMaterial(
            credential_id=credential_id,
            api_key="dummy-api-key",
            key_type=ApiKeyType.HMAC,
            secret=b"dummy-secret",
        )

        provider.put(material)
        loaded = provider.load(credential_id)

        self.assertEqual(loaded, material)
        self.assertNotIn("dummy-secret", repr(loaded))
        self.assertNotIn("dummy-api-key", repr(provider))

    @unittest.skipUnless(sys.platform == "win32", "Windows Credential Manager yalnız Windows’ta çalışır.")
    def test_windows_provider_rejects_unimplemented_key_family(self):
        with self.assertRaisesRegex(SignedRequestError, "CREDENTIAL_KEY_TYPE_UNSUPPORTED"):
            WindowsCredentialManagerProvider(key_type=ApiKeyType.ED25519)


if __name__ == "__main__":
    unittest.main()
