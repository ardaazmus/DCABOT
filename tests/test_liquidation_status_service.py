"""Faz 17 D.2: liquidation-status servisi — venue yoksa SIMULATED_ONLY,
bütçe reddinde önbellekten STALE, okunamayan upstream'de typed hata.
Gerçek ağ çağrısı yok (fake opener + ephemeral credential)."""

import json
import unittest

from dcabot.application.anti_liquidation_status import derive_margin_ratio
from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.liquidation_status_service import (
    LiquidationStatusService,
    LiquidationStatusServiceError,
)
from dcabot.application.signed_request import ApiKeyType


class FixedClock:
    def now_ms(self) -> int:
        return 1_700_000_000_000


class FakeResponse:
    status = 200

    def __init__(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Length": str(len(body))}
        self._body = body

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def close(self) -> None:
        pass


class RoutingOpener:
    """URL'ye göre positionRisk/account yanıtı verir; çağrıları kaydeder."""

    def __init__(self, rows, account):
        self.rows = rows
        self.account = account
        self.calls: list[str] = []

    def open(self, request, timeout: int):
        url = request.full_url
        self.calls.append(url)
        if "positionRisk" in url:
            return FakeResponse(self.rows)
        if "/account" in url:
            return FakeResponse(self.account)
        raise AssertionError(f"beklenmeyen URL: {url}")


ROW = {
    "symbol": "BTCUSDT",
    "positionAmt": "1.000",
    "entryPrice": "60000",
    "markPrice": "60500",
    "liquidationPrice": "54000",
    "leverage": "5",
    "unRealizedProfit": "500",
    "positionSide": "LONG",
    "updateTime": 1_700_000_000_001,
}

ACCOUNT = {
    "totalMaintMargin": "100",
    "totalMarginBalance": "10000",
    "updateTime": 1_700_000_000_001,
}


def _provider() -> EphemeralCredentialProvider:
    provider = EphemeralCredentialProvider()
    provider.put(
        CredentialMaterial(
            credential_id="futures-readonly",
            api_key="dummy-api-key",
            key_type=ApiKeyType.HMAC,
            secret=b"dummy-secret",
        )
    )
    return provider


def _service(**overrides) -> LiquidationStatusService:
    return LiquidationStatusService(
        clock=FixedClock(),
        opener=RoutingOpener([ROW], ACCOUNT),
        **overrides,
    )


class LiquidationStatusServiceTests(unittest.TestCase):
    def test_no_credential_returns_simulated_only_without_network(self):
        opener = RoutingOpener([ROW], ACCOUNT)
        service = LiquidationStatusService(clock=FixedClock(), opener=opener)
        status = service.get_status(
            "BTCUSDT", credential_id=None, provider=None, now_us=1_700_000_000_000_000
        )
        self.assertEqual(status.state, "SIMULATED_ONLY")
        self.assertIsNone(status.liquidation_price)
        self.assertIsNone(status.margin_ratio)
        self.assertFalse(status.is_fast_move)
        self.assertEqual(opener.calls, [])

    def test_empty_rows_mean_no_position(self):
        opener = RoutingOpener([], ACCOUNT)
        service = LiquidationStatusService(clock=FixedClock(), opener=opener)
        status = service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_000_000_000,
        )
        self.assertEqual(status.state, "NO_POSITION")
        self.assertIsNone(status.liquidation_price)

    def test_single_row_returns_data_ok_with_venue_values(self):
        service = _service()
        status = service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_000_000_000,
        )
        self.assertEqual(status.state, "DATA_OK")
        self.assertEqual(status.liquidation_price, "54000")
        self.assertEqual(status.margin_ratio, derive_margin_ratio("100", "10000"))
        self.assertFalse(status.is_fast_move)

    def test_budget_deny_serves_cached_stale(self):
        service = _service(min_interval_us=100_000_000, stale_after_us=10_000_000)
        first = service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_000_000_000,
        )
        self.assertEqual(first.state, "DATA_OK")
        second = service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_050_000_000,
        )
        self.assertEqual(second.state, "STALE")
        self.assertEqual(second.liquidation_price, "54000")
        self.assertIsNotNone(second.margin_ratio)

    def test_second_poll_with_moved_mark_flags_fast_move(self):
        opener = RoutingOpener([dict(ROW, markPrice="60500")], ACCOUNT)
        service = LiquidationStatusService(clock=FixedClock(), opener=opener)
        service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_000_000_000,
        )
        opener.rows = [dict(ROW, markPrice="62500")]
        status = service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_031_000_000,
        )
        self.assertEqual(status.state, "WATCH")
        self.assertTrue(status.is_fast_move)

    def test_hedge_both_sides_is_rejected_not_silently_picked(self):
        rows = [ROW, dict(ROW, positionAmt="-0.5", positionSide="SHORT")]
        opener = RoutingOpener(rows, ACCOUNT)
        service = LiquidationStatusService(clock=FixedClock(), opener=opener)
        with self.assertRaises(LiquidationStatusServiceError) as ctx:
            service.get_status(
                "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
                now_us=1_700_000_000_000_000,
            )
        self.assertEqual(ctx.exception.code, "ALC_MULTI_POSITION_UNSUPPORTED")

    def test_fetch_failure_without_cache_is_typed_error(self):
        class FailingOpener:
            def open(self, request, timeout: int):
                raise ConnectionError("ağ kapalı")

        service = LiquidationStatusService(clock=FixedClock(), opener=FailingOpener())
        with self.assertRaises(LiquidationStatusServiceError) as ctx:
            service.get_status(
                "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
                now_us=1_700_000_000_000_000,
            )
        self.assertEqual(ctx.exception.code, "ALC_UPSTREAM_UNAVAILABLE")

    def test_fetch_failure_with_cache_serves_cached(self):
        opener = RoutingOpener([ROW], ACCOUNT)
        service = LiquidationStatusService(
            clock=FixedClock(), opener=opener,
            min_interval_us=1, stale_after_us=10_000_000,
        )
        service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_000_000_000,
        )

        class FailingOpener:
            def open(self, request, timeout: int):
                raise ConnectionError("ağ kapalı")

        service.opener = FailingOpener()
        status = service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_050_000_000,
        )
        self.assertEqual(status.state, "STALE")
        self.assertEqual(status.liquidation_price, "54000")

    def test_missing_credential_material_is_typed_error(self):
        service = _service()
        with self.assertRaises(LiquidationStatusServiceError) as ctx:
            service.get_status(
                "BTCUSDT", credential_id="yok-boyle-id",
                provider=_provider(), now_us=1_700_000_000_000_000,
            )
        self.assertEqual(ctx.exception.code, "ALC_UPSTREAM_UNAVAILABLE")

    def test_invalid_symbol_is_rejected_before_network(self):
        opener = RoutingOpener([ROW], ACCOUNT)
        service = LiquidationStatusService(clock=FixedClock(), opener=opener)
        for bad in ("", "  ", "X" * 33, "BTC\nUSDT"):
            with self.assertRaises(LiquidationStatusServiceError, msg=repr(bad)) as ctx:
                service.get_status(
                    bad, credential_id="futures-readonly", provider=_provider(),
                    now_us=1_700_000_000_000_000,
                )
            self.assertEqual(ctx.exception.code, "ALC_SYMBOL_INVALID")
        self.assertEqual(opener.calls, [])

    def test_invalid_now_us_is_rejected(self):
        service = _service()
        for bad in (-1, "now", None):
            with self.assertRaises(LiquidationStatusServiceError, msg=repr(bad)):
                service.get_status(
                    "BTCUSDT", credential_id=None, provider=None, now_us=bad,
                )

    def test_budget_deny_without_cache_is_typed_error(self):
        class FailingOpener:
            def open(self, request, timeout: int):
                raise ConnectionError("ağ kapalı")

        service = LiquidationStatusService(clock=FixedClock(), opener=FailingOpener())
        with self.assertRaises(LiquidationStatusServiceError):
            service.get_status(
                "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
                now_us=1_700_000_000_000_000,
            )
        with self.assertRaises(LiquidationStatusServiceError) as ctx:
            service.get_status(
                "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
                now_us=1_700_000_001_000_000,
            )
        self.assertEqual(ctx.exception.code, "ALC_UPSTREAM_UNAVAILABLE")

    def test_credential_without_provider_is_rejected(self):
        service = _service()
        with self.assertRaises(LiquidationStatusServiceError) as ctx:
            service.get_status(
                "BTCUSDT", credential_id="futures-readonly", provider=None,
                now_us=1_700_000_000_000_000,
            )
        self.assertEqual(ctx.exception.code, "ALC_PROVIDER_MISSING")

    def test_regressed_clock_is_wrapped_with_budget_code(self):
        service = _service()
        service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_000_000_000,
        )
        with self.assertRaises(LiquidationStatusServiceError) as ctx:
            service.get_status(
                "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
                now_us=1_700_000_000_000_000 - 1,
            )
        self.assertEqual(ctx.exception.code, "ALC_RATE_BUDGET_CLOCK_REGRESSED")

    def test_invalid_constructor_config_is_rejected(self):
        with self.assertRaises(LiquidationStatusServiceError):
            LiquidationStatusService(stale_after_us=0)
        with self.assertRaises(LiquidationStatusServiceError):
            LiquidationStatusService(fast_move_threshold_per_second="")

    def test_zero_liquidation_price_is_meaningless_not_no_risk(self):
        opener = RoutingOpener([dict(ROW, liquidationPrice="0")], ACCOUNT)
        service = LiquidationStatusService(clock=FixedClock(), opener=opener)
        status = service.get_status(
            "BTCUSDT", credential_id="futures-readonly", provider=_provider(),
            now_us=1_700_000_000_000_000,
        )
        self.assertEqual(status.state, "DATA_OK")
        self.assertIsNone(status.liquidation_price)
        self.assertEqual(status.reason, "LIQUIDATION_PRICE_NOT_MEANINGFUL")


if __name__ == "__main__":
    unittest.main()
