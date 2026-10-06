import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("export_persona", ROOT / "scripts/export_persona.py")
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


class ExportTests(unittest.TestCase):
    def fixture(self, target):
        for rel in ("SOUL.md", "personality.json", "prompts/system.md", "IDENTITY.md", "adapters/AGENTS.fragment.md"):
            path = target / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, path)

    def test_current_sources_are_consistent(self):
        self.assertTrue(exporter.check(ROOT)["ok"])

    def test_crlf_and_lf_export_byte_identically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            self.fixture(root)
            expected = exporter.build_exports(root)
            for path in root.rglob("*"):
                if path.is_file():
                    text = path.read_text(encoding="utf-8")
                    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(expected, exporter.build_exports(root))

    def test_drift_fails_then_explicit_sync_repairs_only_mirrors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            self.fixture(root)
            soul = root / "SOUL.md"
            soul.write_text(soul.read_text(encoding="utf-8") + "\n一条测试性新增正文。\n", encoding="utf-8")
            original = soul.read_bytes()
            identity = (root / "IDENTITY.md").read_bytes()
            self.assertFalse(exporter.check(root)["ok"])
            with self.assertRaises(ValueError):
                exporter.build_exports(root)
            self.assertTrue(exporter.sync(root)["ok"])
            self.assertEqual(soul.read_bytes(), original)
            self.assertEqual((root / "IDENTITY.md").read_bytes(), identity)

    def test_targets_contain_expected_files_without_host_installation(self):
        expected = {
            "prompt": {"prompt.txt"}, "hermes": {"SOUL.md"},
            "openclaw": {"SOUL.md", "IDENTITY.md", "AGENTS.fragment.md"},
            "card-v2": {"character-card-v2.json"}}
        for target, names in expected.items():
            with self.subTest(target=target):
                files, receipt = exporter.build_exports(ROOT, target)
                self.assertEqual(set(files), names | {"README.md"})
                self.assertFalse(receipt["host_settings_modified"])
                self.assertFalse(receipt["host_runtime_verified"])

    def test_card_v2_required_fields_and_no_override(self):
        files, _ = exporter.build_exports(ROOT, "card-v2")
        card = json.loads(files["character-card-v2.json"])
        self.assertEqual((card["spec"], card["spec_version"]), ("chara_card_v2", "2.0"))
        data = card["data"]
        for key in ("name", "description", "personality", "scenario", "first_mes", "mes_example",
                    "creator_notes", "system_prompt", "post_history_instructions", "creator", "character_version"):
            self.assertIsInstance(data[key], str)
        self.assertEqual(data["system_prompt"], "")
        self.assertEqual(data["post_history_instructions"], "")
        self.assertIsInstance(data["alternate_greetings"], list)
        self.assertIsInstance(data["tags"], list)
        self.assertIsInstance(data["extensions"], dict)

    def test_identity_links_resolve_to_repository(self):
        files, _ = exporter.build_exports(ROOT, "openclaw")
        self.assertNotIn("](assets/", files["IDENTITY.md"])
        self.assertIn(exporter.REPOSITORY + "/blob/main/assets/", files["IDENTITY.md"])

    def test_new_directory_and_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "new-export"
            result = exporter.export(ROOT, out)
            self.assertTrue(result["ok"])
            receipt = json.loads((out / "export-manifest.json").read_text(encoding="utf-8"))
            for item in receipt["files"]:
                text = (out / item["path"]).read_text(encoding="utf-8")
                self.assertEqual(exporter.digest(text), item["sha256"])
                self.assertEqual(len(text.encode("utf-8")), item["bytes"])
            before = (out / "SOUL.md").read_bytes()
            with self.assertRaises(ValueError):
                exporter.export(ROOT, out)
            self.assertEqual(before, (out / "SOUL.md").read_bytes())

    def test_existing_empty_directory_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                exporter.export(ROOT, Path(temporary))
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_non_string_mirror_body_is_reported_as_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'
            self.fixture(root)
            path = root / 'personality.json'
            value = json.loads(path.read_text(encoding='utf-8'))
            value['body'] = None
            path.write_text(json.dumps(value), encoding='utf-8')
            self.assertIn('personality_body_drift', exporter.check(root)['errors'])

    def test_source_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'
            self.fixture(root)
            path = root / 'SOUL.md'
            original = root / 'soul-original.txt'
            path.rename(original)
            try:
                path.symlink_to(original)
            except OSError:
                self.skipTest('symlink creation unavailable on this host')
            with self.assertRaisesRegex(ValueError, 'source_symlink'):
                exporter.check(root)


if __name__ == "__main__":
    unittest.main()
