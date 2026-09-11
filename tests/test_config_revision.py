import json
import unittest

from check_workspace import ROOT
from dcabot.application.config_revision import new_config_revision


class ConfigRevisionTests(unittest.TestCase):
    def test_equivalent_config_mapping_order_has_one_canonical_revision(self):
        raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
        reordered = {key: raw[key] for key in reversed(tuple(raw))}

        first = new_config_revision("config-revision-1", raw)
        second = new_config_revision("config-revision-1", reordered)

        self.assertEqual(first, second)

    def test_changed_config_value_has_a_different_revision_hash(self):
        raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
        changed = dict(raw)
        changed["target_quote"] = "2"

        first = new_config_revision("config-revision-1", raw)
        second = new_config_revision("config-revision-2", changed)

        self.assertNotEqual(first.snapshot_sha256, second.snapshot_sha256)
        self.assertNotEqual(first.snapshot_json, second.snapshot_json)


if __name__ == "__main__":
    unittest.main()
