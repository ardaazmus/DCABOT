import unittest

from dcabot.application.paper_orders import (
    PaperOrderError,
    cancel_paper_order,
    fill_paper_order,
    place_paper_order,
)
from dcabot.application.paper_trading_gate import activate_paper_session
from dcabot.data_adapters.public_feed import new_public_observation

HASH = "ab" * 32


def _session(cash="10000"):
    return activate_paper_session(
        confirmed=True,
        session_time_us=1700000000000000,
        symbols=("BTCUSDT",),
        max_staleness_us=5_000_000,
        starting_cash=cash,
        credential_present=False,
    )


def _obs(event_id, price, event_time_us=1700000001000000):
    return new_public_observation(
        source_id="binance-spot-public-v3",
        transport="REST",
        symbol="BTCUSDT",
        product="SPOT",
        event_id=event_id,
        event_time_us=event_time_us,
        receive_time_us=event_time_us + 100,
        processing_time_us=event_time_us + 200,
        price=price,
        quantity="1",
        payload_hash=HASH,
        source_sequence=1,
    )


def _buy(session, order_id="c1", qty="0.01", order_type="MARKET", limit=None):
    return place_paper_order(
        session=session,
        symbol="BTCUSDT",
        side="BUY",
        order_type=order_type,
        qty=qty,
        limit_price=limit,
        client_order_id=order_id,
        order_time_us=1700000000000000,
    )


class PlacePaperOrderTests(unittest.TestCase):
    def test_market_buy_is_new_and_shape_only(self):
        session, order, outcome = _buy(_session())
        self.assertEqual(outcome, "NEW")
        self.assertEqual(order.status, "SIMULATED_NEW")
        self.assertEqual(order.filled_qty, "0")
        self.assertEqual(len(session.orders), 1)
        self.assertEqual(session.cash, "10000")

    def test_exact_repeat_is_duplicate_without_new_state(self):
        session1, order1, _ = _buy(_session())
        session2, order2, outcome = _buy(session1)
        self.assertEqual(outcome, "DUPLICATE")
        self.assertIs(session2, session1)
        self.assertEqual(order2, order1)

    def test_reused_id_with_new_params_conflicts(self):
        session, _, _ = _buy(_session())
        with self.assertRaises(PaperOrderError) as ctx:
            _buy(session, qty="0.02")
        self.assertEqual(ctx.exception.code, "PAPER_ORDER_CONFLICT")

    def test_disallowed_symbol_rejected(self):
        with self.assertRaises(PaperOrderError) as ctx:
            place_paper_order(
                session=_session(), symbol="ETHUSDT", side="BUY",
                order_type="MARKET", qty="1", limit_price=None,
                client_order_id="c1", order_time_us=1700000000000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_SYMBOL_NOT_ALLOWED")

    def test_market_with_limit_price_rejected(self):
        with self.assertRaises(PaperOrderError) as ctx:
            _buy(_session(), limit="50000")
        self.assertEqual(ctx.exception.code, "PAPER_PRICE_INVALID")

    def test_limit_without_price_rejected(self):
        session = _session()
        with self.assertRaises(PaperOrderError) as ctx:
            place_paper_order(
                session=session, symbol="BTCUSDT", side="BUY",
                order_type="LIMIT", qty="0.01", limit_price=None,
                client_order_id="c1", order_time_us=1700000000000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_PRICE_INVALID")


class FillPaperOrderTests(unittest.TestCase):
    def test_full_fill_moves_exact_cash_and_position(self):
        session, _, _ = _buy(_session())
        session, fill, outcome = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e1", "50000"), fill_qty="0.01",
            fill_time_us=1700000002000000,
        )
        self.assertEqual(outcome, "FILLED")
        self.assertEqual(fill.price, "50000")
        self.assertEqual(fill.notional, "500")
        self.assertEqual(session.cash, "9500")
        self.assertEqual(
            [(p.symbol, p.qty) for p in session.positions], [("BTCUSDT", "0.01")]
        )
        self.assertEqual(session.orders[0].status, "SIMULATED_FILLED")

    def test_partial_fills_accumulate_then_close(self):
        session, _, _ = _buy(_session())
        session, _, first = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e1", "50000"), fill_qty="0.004",
            fill_time_us=1700000002000000,
        )
        self.assertEqual(first, "FILLED")
        self.assertEqual(session.orders[0].status, "SIMULATED_PARTIAL")
        session, _, _ = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e2", "50000"), fill_qty="0.006",
            fill_time_us=1700000003000000,
        )
        self.assertEqual(session.orders[0].status, "SIMULATED_FILLED")
        self.assertEqual(session.cash, "9500")

    def test_sell_round_trip_credits_cash_and_clears_position(self):
        session, _, _ = _buy(_session())
        session, _, _ = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e1", "50000"), fill_qty="0.01",
            fill_time_us=1700000002000000,
        )
        session, _, _ = place_paper_order(
            session=session, symbol="BTCUSDT", side="SELL",
            order_type="MARKET", qty="0.01", limit_price=None,
            client_order_id="c2", order_time_us=1700000002000000,
        )
        session, fill, _ = fill_paper_order(
            session=session, client_order_id="c2",
            observation=_obs("e3", "51000"), fill_qty="0.01",
            fill_time_us=1700000004000000,
        )
        self.assertEqual(fill.notional, "510")
        self.assertEqual(session.cash, "10010")
        self.assertEqual(session.positions, ())

    def test_sell_without_position_rejected(self):
        session, _, _ = place_paper_order(
            session=_session(), symbol="BTCUSDT", side="SELL",
            order_type="MARKET", qty="0.01", limit_price=None,
            client_order_id="c9", order_time_us=1700000000000000,
        )
        with self.assertRaises(PaperOrderError) as ctx:
            fill_paper_order(
                session=session, client_order_id="c9",
                observation=_obs("e1", "50000"), fill_qty="0.01",
                fill_time_us=1700000002000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_INSUFFICIENT_POSITION")

    def test_buy_beyond_cash_rejected(self):
        session, _, _ = _buy(_session(), qty="1")
        with self.assertRaises(PaperOrderError) as ctx:
            fill_paper_order(
                session=session, client_order_id="c1",
                observation=_obs("e1", "50000"), fill_qty="1",
                fill_time_us=1700000002000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_INSUFFICIENT_CASH")

    def test_overfill_rejected(self):
        session, _, _ = _buy(_session())
        with self.assertRaises(PaperOrderError) as ctx:
            fill_paper_order(
                session=session, client_order_id="c1",
                observation=_obs("e1", "50000"), fill_qty="0.02",
                fill_time_us=1700000002000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_FILL_QTY_INVALID")

    def test_limit_buy_only_fills_at_or_below_limit(self):
        session, _, _ = _buy(_session(), order_type="LIMIT", limit="49000")
        with self.assertRaises(PaperOrderError) as ctx:
            fill_paper_order(
                session=session, client_order_id="c1",
                observation=_obs("e1", "50000"), fill_qty="0.01",
                fill_time_us=1700000002000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_FILL_PRICE_NOT_TOUCHED")
        session, _, _ = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e2", "48000"), fill_qty="0.01",
            fill_time_us=1700000003000000,
        )
        self.assertEqual(session.cash, "9520")

    def test_exact_repeat_fill_is_duplicate(self):
        session, _, _ = _buy(_session())
        session, fill1, _ = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e1", "50000"), fill_qty="0.01",
            fill_time_us=1700000002000000,
        )
        session2, fill2, outcome = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e1", "50000"), fill_qty="0.01",
            fill_time_us=1700000002000000,
        )
        self.assertEqual(outcome, "DUPLICATE")
        self.assertIs(session2, session)
        self.assertEqual(fill2, fill1)
        self.assertEqual(session.cash, "9500")

    def test_wrong_symbol_observation_rejected(self):
        session, _, _ = _buy(_session())
        eth = new_public_observation(
            source_id="binance-spot-public-v3", transport="REST",
            symbol="ETHUSDT", product="SPOT", event_id="e9",
            event_time_us=1700000001000000, receive_time_us=1700000001000100,
            processing_time_us=1700000001000200, price="3000",
            quantity="1", payload_hash=HASH, source_sequence=1,
        )
        with self.assertRaises(PaperOrderError) as ctx:
            fill_paper_order(
                session=session, client_order_id="c1", observation=eth,
                fill_qty="0.01", fill_time_us=1700000002000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_OBSERVATION_MISMATCH")

    def test_fill_before_source_event_rejected(self):
        session, _, _ = _buy(_session())
        with self.assertRaises(PaperOrderError) as ctx:
            fill_paper_order(
                session=session, client_order_id="c1",
                observation=_obs("e1", "50000", event_time_us=1700000005000000),
                fill_qty="0.01", fill_time_us=1700000002000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_FILL_TIME_INVALID")


class CancelPaperOrderTests(unittest.TestCase):
    def test_cancel_open_order_and_fill_after_cancel_fails(self):
        session, _, _ = _buy(_session())
        session, order = cancel_paper_order(
            session=session, client_order_id="c1",
            cancel_time_us=1700000002000000,
        )
        self.assertEqual(order.status, "SIMULATED_CANCELED")
        with self.assertRaises(PaperOrderError) as ctx:
            fill_paper_order(
                session=session, client_order_id="c1",
                observation=_obs("e1", "50000"), fill_qty="0.01",
                fill_time_us=1700000003000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_ORDER_CLOSED")

    def test_cancel_filled_order_rejected(self):
        session, _, _ = _buy(_session())
        session, _, _ = fill_paper_order(
            session=session, client_order_id="c1",
            observation=_obs("e1", "50000"), fill_qty="0.01",
            fill_time_us=1700000002000000,
        )
        with self.assertRaises(PaperOrderError) as ctx:
            cancel_paper_order(
                session=session, client_order_id="c1",
                cancel_time_us=1700000003000000,
            )
        self.assertEqual(ctx.exception.code, "PAPER_ORDER_CLOSED")


if __name__ == "__main__":
    unittest.main()
