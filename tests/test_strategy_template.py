import hashlib
import unittest

from dcabot.application.strategy_template import (
    StrategyTemplate,
    StrategyTemplateError,
    new_strategy_template,
)


class StrategyTemplateTests(unittest.TestCase):
    def test_template_is_canonical_and_inert(self):
        result = new_strategy_template(
            template_id="dca-basic",
            schema_version="strategy-template-v1",
            payload={"symbol": "BTCUSDT", "amount": "100"},
            declared_capabilities=("DCA", "SPOT"),
        )

        expected_json = '{"amount":"100","symbol":"BTCUSDT"}'
        self.assertEqual(result.payload_json, expected_json)
        self.assertEqual(
            result.payload_sha256, hashlib.sha256(expected_json.encode()).hexdigest()
        )
        self.assertEqual(result.declared_capabilities, ("DCA", "SPOT"))
        self.assertFalse(hasattr(result, "orders"))
        self.assertFalse(hasattr(result, "activate"))

    def test_mapping_order_does_not_change_template_identity(self):
        first = new_strategy_template(
            template_id="dca-basic",
            schema_version="strategy-template-v1",
            payload={"b": "2", "a": "1"},
            declared_capabilities=("SPOT", "DCA"),
        )
        second = new_strategy_template(
            template_id="dca-basic",
            schema_version="strategy-template-v1",
            payload={"a": "1", "b": "2"},
            declared_capabilities=("DCA", "SPOT"),
        )

        self.assertEqual(first, second)

    def test_tampered_hash_or_noncanonical_snapshot_is_rejected(self):
        with self.assertRaisesRegex(
            StrategyTemplateError, "TEMPLATE_HASH_MISMATCH"
        ):
            StrategyTemplate(
                template_id="dca-basic",
                schema_version="strategy-template-v1",
                payload_json='{"a":"1"}',
                payload_sha256="a" * 64,
                declared_capabilities=("DCA",),
            )
        with self.assertRaisesRegex(
            StrategyTemplateError, "TEMPLATE_SNAPSHOT_INVALID"
        ):
            StrategyTemplate(
                template_id="dca-basic",
                schema_version="strategy-template-v1",
                payload_json='{"b":"2","a":"1"}',
                payload_sha256=hashlib.sha256(
                    b'{"b":"2","a":"1"}'
                ).hexdigest(),
                declared_capabilities=("DCA",),
            )

    def test_secret_executable_float_and_duplicate_capability_inputs_fail_closed(self):
        cases = (
            ({"api_key": "hidden"}, "TEMPLATE_FORBIDDEN_FIELD"),
            ({"script": "run()"}, "TEMPLATE_FORBIDDEN_FIELD"),
            ({"weight": 0.5}, "TEMPLATE_PAYLOAD_INVALID"),
        )
        for payload, code in cases:
            with self.subTest(payload=payload), self.assertRaisesRegex(
                StrategyTemplateError, code
            ):
                new_strategy_template(
                    template_id="dca-basic",
                    schema_version="strategy-template-v1",
                    payload=payload,
                    declared_capabilities=("DCA",),
                )
        with self.assertRaisesRegex(
            StrategyTemplateError, "TEMPLATE_CAPABILITY_DUPLICATE"
        ):
            new_strategy_template(
                template_id="dca-basic",
                schema_version="strategy-template-v1",
                payload={},
                declared_capabilities=("DCA", "DCA"),
            )

    def test_direct_template_constructor_rejects_duplicate_capabilities(self):
        with self.assertRaisesRegex(
            StrategyTemplateError, "TEMPLATE_CAPABILITY_DUPLICATE"
        ):
            StrategyTemplate(
                template_id="dca-basic",
                schema_version="strategy-template-v1",
                payload_json="{}",
                payload_sha256=hashlib.sha256(b"{}").hexdigest(),
                declared_capabilities=("DCA", "DCA"),
            )

    def test_schema_and_payload_size_are_bounded(self):
        with self.assertRaisesRegex(
            StrategyTemplateError, "TEMPLATE_SCHEMA_INVALID"
        ):
            new_strategy_template(
                template_id="dca-basic",
                schema_version="strategy-template-v2",
                payload={},
                declared_capabilities=("DCA",),
            )
        with self.assertRaisesRegex(
            StrategyTemplateError, "TEMPLATE_PAYLOAD_TOO_LARGE"
        ):
            new_strategy_template(
                template_id="dca-basic",
                schema_version="strategy-template-v1",
                payload={"note": "x" * 70_000},
                declared_capabilities=("DCA",),
            )
