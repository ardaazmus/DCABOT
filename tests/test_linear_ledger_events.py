import unittest

from dcabot.application.linear_futures_math import (
    LinearLedgerEvent,
    apply_linear_ledger_event,
    funding_expense_from_cashflow,
    net_realized_result,
    new_linear_ledger_state,
)


def fee(event_id="fee-1", amount="0.5", time_us=1_000):
    return LinearLedgerEvent(
        event_id=event_id,
        event_type="TRADING_FEE",
        effective_time_us=time_us,
        settlement_asset="USDT",
        amount=amount,
    )


def funding(event_id="funding-1", amount="-5.25", time_us=2_000):
    return LinearLedgerEvent(
        event_id=event_id,
        event_type="FUNDING",
        effective_time_us=time_us,
        settlement_asset="USDT",
        amount=amount,
    )


class LinearLedgerEventTests(unittest.TestCase):
    def test_fee_and_funding_remain_separate_and_bind_to_net_result(self):
        state = new_linear_ledger_state("USDT")
        state = apply_linear_ledger_event(state, fee())
        state = apply_linear_ledger_event(state, funding())

        self.assertEqual(state.fee_expense, "0.5")
        self.assertEqual(state.funding_cashflow, "-5.25")
        self.assertEqual(net_realized_result("1500", state), "1494.25")

    def test_exact_duplicate_is_idempotent_and_conflicting_duplicate_is_rejected(self):
        state = apply_linear_ledger_event(
            new_linear_ledger_state("USDT"), funding()
        )
        self.assertEqual(apply_linear_ledger_event(state, funding()), state)

        with self.assertRaisesRegex(ValueError, "LINEAR_LEDGER_DUPLICATE_CONFLICT"):
            apply_linear_ledger_event(state, funding(amount="5.25"))

    def test_new_event_must_be_time_ordered_and_asset_matched(self):
        state = apply_linear_ledger_event(
            new_linear_ledger_state("USDT"), funding(time_us=2_000)
        )
        with self.assertRaisesRegex(ValueError, "LINEAR_LEDGER_EVENT_ORDER"):
            apply_linear_ledger_event(state, fee(time_us=1_000))
        with self.assertRaisesRegex(ValueError, "LINEAR_LEDGER_ASSET_INVALID"):
            apply_linear_ledger_event(
                new_linear_ledger_state("USDT"),
                LinearLedgerEvent("fee-1", "TRADING_FEE", 1_000, "BTC", "0.5"),
            )

def test_funding_cashflow_requires_explicit_core_expense_conversion(self):
        self.assertEqual(funding_expense_from_cashflow("-5.25"), "5.25")
        self.assertEqual(funding_expense_from_cashflow("5.25"), "-5.25")


if __name__ == "__main__":
    unittest.main()
