import hashlib
import hmac
import unittest

from dcabot.application.signed_request import (
    ApiKeyType,
    Clock,
    HmacSha256Signer,
    SignedRequestError,
    build_signed_request,
    is_timestamp_within_window,
    validate_recv_window_ms,
)


class FixedClock:
    def __init__(self, timestamp_ms: int):
        self.timestamp_ms = timestamp_ms

    def now_ms(self) -> int:
        return self.timestamp_ms


class UnknownSigner:
    key_type = ApiKeyType.UNKNOWN

    def sign(self, _payload: bytes) -> str:
        return "not-used"


class SignedRequestTests(unittest.TestCase):
    def test_hmac_signer_matches_independent_sha256_oracle(self):
        signer = HmacSha256Signer(b"dummy-test-key")
        payload = b"symbol=BTCUSDT&timestamp=1700000000000"

        expected = hmac.new(b"dummy-test-key", payload, hashlib.sha256).hexdigest()

        self.assertEqual(signer.sign(payload), expected)
        self.assertEqual(signer.key_type, ApiKeyType.HMAC)
        self.assertNotIn("dummy-test-key", repr(signer))

    def test_signed_request_preserves_exact_encoded_payload_and_signature(self):
        signer = HmacSha256Signer(b"dummy-test-key")
        request = build_signed_request(
            (("symbol", "１２３４５６"), ("side", "BUY")),
            clock=FixedClock(1_700_000_000_000),
            recv_window_ms=5_000,
            signer=signer,
        )

        expected_payload = (
            "symbol=%EF%BC%91%EF%BC%92%EF%BC%93%EF%BC%94%EF%BC%95%EF%BC%96"
            "&side=BUY&timestamp=1700000000000&recvWindow=5000"
        )
        expected_signature = hmac.new(
            b"dummy-test-key", expected_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()

        self.assertEqual(request.payload, expected_payload)
        self.assertEqual(request.signature, expected_signature)
        self.assertEqual(request.key_type, ApiKeyType.HMAC)
        self.assertNotIn("dummy-test-key", repr(request))

    def test_signed_request_rejects_unsafe_or_duplicate_parameters(self):
        signer = HmacSha256Signer(b"dummy-test-key")
        for params in (
            (("apiKey", "not-a-secret"),),
            (("signature", "caller-supplied"),),
            (("timestamp", "1700000000000"),),
            (("symbol", "BTCUSDT"), ("symbol", "ETHUSDT")),
        ):
            with self.subTest(params=params):
                with self.assertRaisesRegex(SignedRequestError, "SIGNED_PARAM_UNSAFE"):
                    build_signed_request(
                        params,
                        clock=FixedClock(1_700_000_000_000),
                        recv_window_ms=5_000,
                        signer=signer,
                    )

    def test_signed_request_rejects_unknown_key_type(self):
        with self.assertRaisesRegex(SignedRequestError, "SIGNED_KEY_TYPE_UNSUPPORTED"):
            build_signed_request(
                (("symbol", "BTCUSDT"),),
                clock=FixedClock(1_700_000_000_000),
                recv_window_ms=5_000,
                signer=UnknownSigner(),
            )

    def test_recv_window_is_positive_integer_and_cannot_exceed_policy_limit(self):
        self.assertEqual(validate_recv_window_ms(1), 1)
        self.assertEqual(validate_recv_window_ms(60_000), 60_000)
        for value in (0, -1, 60_001, True, 5_000.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(SignedRequestError, "RECV_WINDOW_INVALID"):
                    validate_recv_window_ms(value)

    def test_timestamp_window_uses_server_time_and_one_second_future_tolerance(self):
        server_time_ms = 1_700_000_000_000
        recv_window_ms = 5_000

        self.assertTrue(
            is_timestamp_within_window(
                server_time_ms, server_time_ms, recv_window_ms
            )
        )
        self.assertTrue(
            is_timestamp_within_window(
                server_time_ms - recv_window_ms, server_time_ms, recv_window_ms
            )
        )
        self.assertTrue(
            is_timestamp_within_window(
                server_time_ms + 999, server_time_ms, recv_window_ms
            )
        )
        self.assertFalse(
            is_timestamp_within_window(
                server_time_ms - recv_window_ms - 1,
                server_time_ms,
                recv_window_ms,
            )
        )
        self.assertFalse(
            is_timestamp_within_window(
                server_time_ms + 1_000, server_time_ms, recv_window_ms
            )
        )


if __name__ == "__main__":
    unittest.main()
