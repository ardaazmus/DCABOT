"""TradingView webhook intake: static-token auth and durable dedup identity.

TradingView cannot sign requests (no custom headers, no HMAC): the only
realistic wire guard is a long random shared secret embedded in the JSON
message body, compared in constant time. ``verify_signal_signature``
(HMAC) stays reserved for DCABOT's own relay/internal clients.

This module is pure: no wall clock, no environment, no logging. The API
layer supplies the expected token (from env) and the receipt timestamp.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import re


_SOURCE = "tradingview"
_INTERNAL_SOURCE = "internal-relay"
_SYMBOL = re.compile(r"[A-Z0-9:_-]{1,32}\Z", re.ASCII)
_ACTION = re.compile(r"[A-Za-z0-9:_-]{1,32}\Z", re.ASCII)
_ORDER_ID = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_PRICE = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z", re.ASCII)
_ISO_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z", re.ASCII)
_ALLOWED_FIELDS = frozenset({"secret", "symbol", "action", "event_time_us", "price", "strategy_order_id"})
_INTERNAL_ALLOWED_FIELDS = frozenset({"symbol", "action", "event_time_us", "price", "strategy_order_id"})


class TradingViewWebhookError(ValueError):
    """Raised when a webhook alert cannot be authenticated or identified."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class TradingViewAlert:
    """One validated alert. The wire secret is never stored on the alert."""

    source: str
    symbol: str
    action: str
    event_time_us: int
    price: str | None
    strategy_order_id: str | None


def parse_tradingview_alert(payload: object) -> TradingViewAlert:
    """Validate the narrow TradingView JSON contract without authenticating."""

    if not isinstance(payload, dict):
        raise TradingViewWebhookError("WEBHOOK_BODY_INVALID", "Webhook gövdesi JSON nesnesi olmalıdır.")
    unknown = set(payload) - _ALLOWED_FIELDS
    if unknown:
        raise TradingViewWebhookError("WEBHOOK_FIELD_UNKNOWN", "Webhook alanında bilinmeyen anahtar var.")
    for name in ("secret", "symbol", "action", "event_time_us"):
        if name not in payload:
            raise TradingViewWebhookError("WEBHOOK_FIELD_MISSING", f"Webhook alanında {name} zorunludur.")
    if not isinstance(payload["secret"], str) or not payload["secret"]:
        raise TradingViewWebhookError("WEBHOOK_SECRET_INVALID", "Webhook secret metni geçersiz.")
    symbol = payload["symbol"]
    if not isinstance(symbol, str) or _SYMBOL.fullmatch(symbol) is None:
        raise TradingViewWebhookError("WEBHOOK_SYMBOL_INVALID", "Webhook symbol biçimi geçersiz.")
    action = payload["action"]
    if not isinstance(action, str) or _ACTION.fullmatch(action) is None:
        raise TradingViewWebhookError("WEBHOOK_ACTION_INVALID", "Webhook action biçimi geçersiz.")
    event_time_us = _parse_time(payload["event_time_us"])
    price = payload.get("price")
    if price is not None and (not isinstance(price, str) or _PRICE.fullmatch(price) is None):
        raise TradingViewWebhookError("WEBHOOK_PRICE_INVALID", "Webhook price exact decimal metni olmalıdır.")
    order_id = payload.get("strategy_order_id")
    if order_id is not None and (not isinstance(order_id, str) or _ORDER_ID.fullmatch(order_id) is None):
        raise TradingViewWebhookError("WEBHOOK_ORDER_ID_INVALID", "Webhook strategy_order_id biçimi geçersiz.")
    return TradingViewAlert(
        source=_SOURCE,
        symbol=symbol,
        action=action,
        event_time_us=event_time_us,
        price=price,
        strategy_order_id=order_id,
    )


def parse_internal_alert(payload: object) -> TradingViewAlert:
    """Validate the secret-free relay shape (HMAC is verified separately).

    The source is ``internal-relay`` so relay deliveries never share a
    dedup key with the TradingView wire stream.
    """

    if not isinstance(payload, dict):
        raise TradingViewWebhookError("WEBHOOK_BODY_INVALID", "Webhook gövdesi JSON nesnesi olmalıdır.")
    unknown = set(payload) - _INTERNAL_ALLOWED_FIELDS
    if unknown:
        raise TradingViewWebhookError("WEBHOOK_FIELD_UNKNOWN", "Webhook alanında bilinmeyen anahtar var.")
    for name in ("symbol", "action", "event_time_us"):
        if name not in payload:
            raise TradingViewWebhookError("WEBHOOK_FIELD_MISSING", f"Webhook alanında {name} zorunludur.")
    symbol = payload["symbol"]
    if not isinstance(symbol, str) or _SYMBOL.fullmatch(symbol) is None:
        raise TradingViewWebhookError("WEBHOOK_SYMBOL_INVALID", "Webhook symbol biçimi geçersiz.")
    action = payload["action"]
    if not isinstance(action, str) or _ACTION.fullmatch(action) is None:
        raise TradingViewWebhookError("WEBHOOK_ACTION_INVALID", "Webhook action biçimi geçersiz.")
    event_time_us = _parse_time(payload["event_time_us"])
    price = payload.get("price")
    if price is not None and (not isinstance(price, str) or _PRICE.fullmatch(price) is None):
        raise TradingViewWebhookError("WEBHOOK_PRICE_INVALID", "Webhook price exact decimal metni olmalıdır.")
    order_id = payload.get("strategy_order_id")
    if order_id is not None and (not isinstance(order_id, str) or _ORDER_ID.fullmatch(order_id) is None):
        raise TradingViewWebhookError("WEBHOOK_ORDER_ID_INVALID", "Webhook strategy_order_id biçimi geçersiz.")
    return TradingViewAlert(
        source=_INTERNAL_SOURCE,
        symbol=symbol,
        action=action,
        event_time_us=event_time_us,
        price=price,
        strategy_order_id=order_id,
    )


def verify_webhook_token(*, presented: object, expected: object) -> None:
    """Compare the body-embedded secret in constant time.

    Any failure raises the same error without revealing which side was
    wrong or what the expected value was.
    """

    if (
        not isinstance(presented, str)
        or not isinstance(expected, str)
        or not presented
        or not expected
        or not hmac.compare_digest(presented, expected)
    ):
        raise TradingViewWebhookError("WEBHOOK_TOKEN_MISMATCH", "Webhook kimliği doğrulanamadı.")


def webhook_dedup_key(alert: TradingViewAlert) -> str:
    """Return the composite dedup key for one alert.

    Price is deliberately excluded: two deliveries of the same bar alert
    may format the price differently. When the strategy provides its own
    order id (``strategy.order.id``), it replaces the bar timestamp as the
    time reference so two alerts on the same bar stay distinct.
    """

    if not isinstance(alert, TradingViewAlert):
        raise TradingViewWebhookError("WEBHOOK_ALERT_INVALID", "Webhook alert güvenli tipte olmalıdır.")
    time_ref = alert.strategy_order_id if alert.strategy_order_id is not None else str(alert.event_time_us)
    return f"{alert.source}|{alert.symbol}|{alert.action}|{time_ref}"


def webhook_signal_id(alert: TradingViewAlert) -> str:
    """Derive the deterministic signal id from the dedup key."""

    digest = hashlib.sha256(webhook_dedup_key(alert).encode("utf-8")).hexdigest()
    return f"tv-{digest[:32]}"


def canonical_alert_payload(alert: TradingViewAlert) -> dict[str, object]:
    """Return the canonical payload hashed by ``hash_signal_payload``.

    Unlike the dedup key, this includes the price: the hash binds the
    accepted content, while the key binds the delivery identity.
    """

    if not isinstance(alert, TradingViewAlert):
        raise TradingViewWebhookError("WEBHOOK_ALERT_INVALID", "Webhook alert güvenli tipte olmalıdır.")
    payload: dict[str, object] = {
        "source": alert.source,
        "symbol": alert.symbol,
        "action": alert.action,
        "event_time_us": alert.event_time_us,
    }
    if alert.price is not None:
        payload["price"] = alert.price
    if alert.strategy_order_id is not None:
        payload["strategy_order_id"] = alert.strategy_order_id
    return payload


def _parse_time(value: object) -> int:
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and _ISO_UTC.fullmatch(value) is not None:
        try:
            moment = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError as error:
            raise TradingViewWebhookError("WEBHOOK_TIME_INVALID", "Webhook zamanı geçersiz.") from error
        return int(moment.timestamp() * 1_000_000)
    raise TradingViewWebhookError("WEBHOOK_TIME_INVALID", "Webhook zamanı µs integer veya UTC ISO-8601 olmalıdır.")
