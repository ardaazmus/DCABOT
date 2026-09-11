import unittest

from dcabot.application.strategy_template import new_strategy_template
from dcabot.application.template_activation_gate import (
    TemplateActivationError,
    TemplateActivationDecision,
    assess_template_activation,
)


def template():
    return new_strategy_template(
        template_id="dca-basic",
        schema_version="strategy-template-v1",
        payload={"symbol": "BTCUSDT"},
        declared_capabilities=("DCA", "SPOT"),
    )


class TemplateActivationGateTests(unittest.TestCase):
    def test_supported_capabilities_wait_for_explicit_approval(self):
        result = assess_template_activation(
            template(), allowed_capabilities=("SPOT", "DCA"), approval="PENDING"
        )

        self.assertEqual(
            result,
            TemplateActivationDecision(
                template_id="dca-basic",
                status="AWAITING_APPROVAL",
                declared_capabilities=("DCA", "SPOT"),
                unsupported_capabilities=(),
            ),
        )

    def test_approved_capabilities_only_become_ready_for_activation(self):
        result = assess_template_activation(
            template(), allowed_capabilities=("DCA", "SPOT"), approval="APPROVED"
        )

        self.assertEqual(result.status, "READY_FOR_ACTIVATION")
        self.assertFalse(hasattr(result, "orders"))
        self.assertFalse(hasattr(result, "fills"))

    def test_unsupported_capability_is_blocked_before_approval(self):
        result = assess_template_activation(
            template(), allowed_capabilities=("SPOT",), approval="APPROVED"
        )

        self.assertEqual(
            result,
            TemplateActivationDecision(
                template_id="dca-basic",
                status="CAPABILITY_UNSUPPORTED",
                declared_capabilities=("DCA", "SPOT"),
                unsupported_capabilities=("DCA",),
            ),
        )

    def test_invalid_approval_or_allowlist_fails_closed(self):
        with self.assertRaisesRegex(
            TemplateActivationError, "TEMPLATE_APPROVAL_INVALID"
        ):
            assess_template_activation(
                template(), allowed_capabilities=("DCA", "SPOT"), approval="YES"
            )
        with self.assertRaisesRegex(
            TemplateActivationError, "TEMPLATE_ALLOWED_CAPABILITY_DUPLICATE"
        ):
            assess_template_activation(
                template(), allowed_capabilities=("DCA", "DCA"), approval="PENDING"
            )

