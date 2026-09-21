import unittest

from dcabot.application.strategy_template import new_strategy_template
from dcabot.application.template_profile_binding import (
    TemplateBinding,
    TemplateBindingError,
    bind_template_to_profile,
)


def _template(payload, capabilities=("DCA", "SPOT")):
    return new_strategy_template(
        template_id="dca-basic",
        schema_version="strategy-template-v1",
        payload=payload,
        declared_capabilities=capabilities,
    )


def _bind(template, **overrides):
    params = {
        "template": template,
        "profile_id": "paper",
        "allowed_capabilities": ("DCA", "SPOT"),
        "approval": "APPROVED",
        "binding_time_us": 1700000000000000,
    }
    params.update(overrides)
    return bind_template_to_profile(**params)


class BindTemplateToProfileTests(unittest.TestCase):
    def test_valid_binding_is_deterministic_and_canonical(self):
        template = _template({"deviation": "0.1", "base_qty": "0.001"})
        first = _bind(template)
        second = _bind(template)
        self.assertIsInstance(first, TemplateBinding)
        self.assertEqual(first.status, "BOUND")
        self.assertEqual(first.template_id, "dca-basic")
        self.assertEqual(first.profile_id, "paper")
        self.assertEqual(
            first.params, (("base_qty", "0.001"), ("deviation", "0.1"))
        )
        self.assertEqual(first.binding_id, second.binding_id)
        self.assertRegex(first.binding_id, r"\A[0-9a-f]{64}\Z")

    def test_binding_id_changes_with_profile(self):
        template = _template({"deviation": "0.1"})
        base = _bind(template)
        other = _bind(template, profile_id="historical_demo_btcusdt_1h_v1")
        self.assertNotEqual(base.binding_id, other.binding_id)

    def test_pending_approval_cannot_bind(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({"deviation": "0.1"}), approval="PENDING")
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_NOT_READY")

    def test_unsupported_capability_cannot_bind(self):
        template = _template({"deviation": "0.1"}, capabilities=("DCA", "MARGIN"))
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(template)
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_NOT_READY")

    def test_unknown_profile_rejected(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({"deviation": "0.1"}), profile_id="nope")
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_PROFILE_UNKNOWN")

    def test_venue_owned_param_rejected(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({"tick": "0.01"}))
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_PARAM_UNKNOWN")

    def test_risk_owned_param_rejected(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({"leverage": "2"}))
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_PARAM_UNKNOWN")

    def test_out_of_range_value_rejected(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({"deviation": "1.5"}))
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_PARAM_INVALID")

    def test_safety_count_must_be_integer(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({"safety_count": "3"}))
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_PARAM_INVALID")

    def test_safety_count_range_enforced(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({"safety_count": 51}))
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_PARAM_INVALID")

    def test_empty_payload_cannot_bind(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind(_template({}))
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_EMPTY")

    def test_non_template_rejected(self):
        with self.assertRaises(TemplateBindingError) as ctx:
            _bind({"deviation": "0.1"})
        self.assertEqual(ctx.exception.code, "TEMPLATE_BINDING_TEMPLATE_INVALID")


if __name__ == "__main__":
    unittest.main()
