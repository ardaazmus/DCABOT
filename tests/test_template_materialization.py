import json
import tempfile
import unittest
from pathlib import Path

from dcabot.application.strategy_template import new_strategy_template
from dcabot.application.template_materialization import (
    TemplateFileStore,
    TemplateMaterializationError,
    diff_templates,
    materialize_binding,
)
from dcabot.application.template_profile_binding import bind_template_to_profile

ROOT = Path(__file__).resolve().parents[1]


def _bound(payload, profile_id="paper"):
    template = new_strategy_template(
        template_id="t1",
        schema_version="strategy-template-v1",
        payload=payload,
        declared_capabilities=("DCA", "SPOT"),
    )
    return bind_template_to_profile(
        template=template,
        profile_id=profile_id,
        allowed_capabilities=("DCA", "SPOT"),
        approval="APPROVED",
        binding_time_us=1700000000000000,
    )


class MaterializeBindingTests(unittest.TestCase):
    def test_override_merges_and_hashes_stably(self):
        binding = _bound({"deviation": "0.2"})
        first = materialize_binding(binding, ROOT)
        second = materialize_binding(binding, ROOT)
        self.assertEqual(first.profile_id, "paper")
        self.assertEqual(first.config["deviation"], "0.2")
        self.assertEqual(first.config["base_qty"], "1")
        self.assertEqual(first.config_hash, second.config_hash)
        self.assertRegex(first.config_hash, r"\A[0-9a-f]{64}\Z")

    def test_off_grid_override_fails_closed(self):
        binding = _bound({"base_qty": "0.0005"})
        with self.assertRaises(TemplateMaterializationError) as ctx:
            materialize_binding(binding, ROOT)
        self.assertEqual(ctx.exception.code, "TEMPLATE_MATERIALIZE_CONFIG_INVALID")

    def test_unknown_profile_binding_rejected(self):
        binding = _bound({"deviation": "0.2"})
        with self.assertRaises(TemplateMaterializationError) as ctx:
            materialize_binding(binding, ROOT / "nonexistent-root")
        self.assertEqual(ctx.exception.code, "TEMPLATE_MATERIALIZE_CONFIG_INVALID")


class TemplateFileStoreTests(unittest.TestCase):
    def _store(self, tmp):
        return TemplateFileStore(Path(tmp) / "templates")

    def test_save_load_round_trip(self):
        template = new_strategy_template(
            template_id="t1",
            schema_version="strategy-template-v1",
            payload={"deviation": "0.2"},
            declared_capabilities=("DCA",),
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            path = store.save(template)
            self.assertTrue(str(path).endswith("t1.json"))
            self.assertEqual(store.load("t1"), template)
            self.assertEqual(store.list_ids(), ("t1",))

    def test_import_validates_and_export_round_trips(self):
        body = json.dumps(
            {
                "template_id": "imp1",
                "schema_version": "strategy-template-v1",
                "payload": {"deviation": "0.2"},
                "declared_capabilities": ["DCA"],
            }
        ).encode()
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            template = store.import_bytes(body)
            self.assertEqual(template.template_id, "imp1")
            exported = store.export_bytes("imp1")
            self.assertEqual(store.import_bytes(exported), template)

    def test_import_rejects_forbidden_keys(self):
        body = json.dumps(
            {
                "template_id": "bad",
                "schema_version": "strategy-template-v1",
                "payload": {"api_key": "x"},
                "declared_capabilities": ["DCA"],
            }
        ).encode()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TemplateMaterializationError) as ctx:
                self._store(tmp).import_bytes(body)
            self.assertEqual(ctx.exception.code, "TEMPLATE_IMPORT_INVALID")

    def test_load_unknown_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TemplateMaterializationError) as ctx:
                self._store(tmp).load("nope")
            self.assertEqual(ctx.exception.code, "TEMPLATE_NOT_FOUND")


class DiffTemplatesTests(unittest.TestCase):
    def _template(self, payload):
        return new_strategy_template(
            template_id="t",
            schema_version="strategy-template-v1",
            payload=payload,
            declared_capabilities=("DCA",),
        )

    def test_changed_added_removed_keys(self):
        old = self._template({"a": "1", "b": "2"})
        new = self._template({"b": "3", "c": "4"})
        self.assertEqual(
            diff_templates(old, new),
            (("a", "1", None), ("b", "2", "3"), ("c", None, "4")),
        )

    def test_identical_payloads_have_empty_diff(self):
        template = self._template({"a": "1"})
        self.assertEqual(diff_templates(template, template), ())


if __name__ == "__main__":
    unittest.main()
