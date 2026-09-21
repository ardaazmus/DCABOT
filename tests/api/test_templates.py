import tempfile
import unittest
from pathlib import Path

from dcabot.application.template_materialization import TemplateFileStore
from dcabot.server.api import (
    _template_bind,
    _template_diff,
    _template_import,
    _validate_template_bind_payload,
    _validate_template_diff_payload,
    _validate_template_import_payload,
)


def _store(tmp):
    return TemplateFileStore(Path(tmp) / "templates")


def _doc(payload=None, template_id="t1"):
    return {
        "template_id": template_id,
        "schema_version": "strategy-template-v1",
        "payload": payload or {"deviation": "0.2"},
        "declared_capabilities": ["DCA", "SPOT"],
    }


class TemplateImportTests(unittest.TestCase):
    def test_valid_import_returns_meta(self):
        validated, fields = _validate_template_import_payload(_doc())
        self.assertEqual(fields, {})
        with tempfile.TemporaryDirectory() as tmp:
            meta = _template_import(_store(tmp), validated)
        self.assertEqual(meta["template_id"], "t1")
        self.assertRegex(meta["payload_sha256"], r"\A[0-9a-f]{64}\Z")
        self.assertEqual(meta["declared_capabilities"], ["DCA", "SPOT"])

    def test_wrong_schema_is_field_error(self):
        doc = _doc()
        doc["schema_version"] = "v9"
        validated, fields = _validate_template_import_payload(doc)
        self.assertIsNone(validated)
        self.assertIn("schema_version", fields)

    def test_forbidden_payload_key_surfaces_as_value_error(self):
        doc = _doc({"api_key": "x"})
        validated, fields = _validate_template_import_payload(doc)
        self.assertEqual(fields, {})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as ctx:
                _template_import(_store(tmp), validated)
        self.assertIn("TEMPLATE_", str(ctx.exception))


class TemplateBindTests(unittest.TestCase):
    def test_bind_returns_binding_and_materialized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = _store(tmp)
            validated, _ = _validate_template_import_payload(_doc())
            _template_import(store, validated)
            bind, fields = _validate_template_bind_payload(
                {
                    "profile_id": "paper",
                    "allowed_capabilities": ["DCA", "SPOT"],
                    "approval": "APPROVED",
                }
            )
            self.assertEqual(fields, {})
            result = _template_bind(store, "t1", bind, 1700000000000000)
        self.assertEqual(result["binding"]["status"], "BOUND")
        self.assertEqual(
            result["binding"]["params"], [["deviation", "0.2"]]
        )
        self.assertEqual(result["materialized"]["config"]["deviation"], "0.2")
        self.assertRegex(result["materialized"]["config_hash"], r"\A[0-9a-f]{64}\Z")

    def test_bind_unknown_template_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as ctx:
                _template_bind(
                    _store(tmp), "nope",
                    {
                        "profile_id": "paper",
                        "allowed_capabilities": ["DCA", "SPOT"],
                        "approval": "APPROVED",
                    },
                    1700000000000000,
                )
        self.assertIn("TEMPLATE_NOT_FOUND", str(ctx.exception))


class TemplateDiffTests(unittest.TestCase):
    def test_diff_rows_are_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = _store(tmp)
            for tid, payload in (
                ("a", {"x": "1", "y": "2"}),
                ("b", {"y": "3", "z": "4"}),
            ):
                validated, _ = _validate_template_import_payload(_doc(payload, tid))
                _template_import(store, validated)
            validated, fields = _validate_template_diff_payload(
                {"first_id": "a", "second_id": "b"}
            )
            self.assertEqual(fields, {})
            rows = _template_diff(store, validated)
        self.assertEqual(
            rows,
            [
                {"key": "x", "before": "1", "after": None},
                {"key": "y", "before": "2", "after": "3"},
                {"key": "z", "before": None, "after": "4"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
