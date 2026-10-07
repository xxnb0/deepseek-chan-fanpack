import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PET = Path("assets/pets/chatgpt")
SPEC = importlib.util.spec_from_file_location("verify_pet", ROOT / "scripts/verify.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class PetManifestTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.pet = self.root / PET
        # Report consistency is testable offline without pretending to inspect pixels.
        shutil.copytree(ROOT / PET, self.pet,
                        ignore=shutil.ignore_patterns("*.png", "*.gif", "*.mp4"))
        self.manifest = json.loads((self.pet / "manifest.json").read_text(encoding="utf-8"))
        self.known = {
            (PET / item["path"]).as_posix(): {
                "bytes": item["bytes"], "sha256": item["sha256"], "tier": "core"
            }
            for item in self.manifest["formats"].values()
        }

    def save_manifest(self):
        (self.pet / "manifest.json").write_text(
            json.dumps(self.manifest), encoding="utf-8")

    def change_json(self, relative, change):
        path = self.pet / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_published_metadata_and_reviewed_warnings_are_consistent(self):
        stats, errors = VERIFY.verify_pet_manifest(self.root, self.known)
        self.assertEqual(errors, [])
        self.assertEqual(stats["pet_formats_metadata_checked"], 2)
        # An accepted warning is not silently converted into a clean visual result.
        quality = json.loads((self.pet / self.manifest["quality_report"]).read_text(encoding="utf-8"))
        self.assertTrue(quality["warnings"])
        self.assertEqual(stats["pet_quality_report_warnings"], len(quality["warnings"]))

    def test_main_manifest_must_cover_each_atlas(self):
        missing = (PET / self.manifest["formats"]["v2"]["path"]).as_posix()
        self.known.pop(missing)
        _, errors = VERIFY.verify_pet_manifest(self.root, self.known)
        self.assertIn("Pet atlas missing from core manifest: v2", errors)

    def test_new_atlas_hash_cannot_reuse_old_pass_reports(self):
        item = self.manifest["formats"]["v2"]
        item["sha256"] = "0" * 64
        self.known[(PET / item["path"]).as_posix()]["sha256"] = item["sha256"]
        self.save_manifest()
        _, errors = VERIFY.verify_pet_manifest(self.root, self.known)
        self.assertIn("Pet structural report mismatch: v2/sha256", errors)
        self.assertIn("Pet MCP report mismatch: v2/sha256", errors)
        self.assertIn("Pet quality report mismatch: sha256", errors)

    def test_mcp_failure_cannot_be_overridden_by_manifest_claim(self):
        report = self.manifest["formats"]["v2"]["mcp_read_only_validation"]
        self.change_json(report, lambda data: data["result"]["structuredContent"].update(
            valid=False, errors=["changed atlas"]))
        _, errors = VERIFY.verify_pet_manifest(self.root, self.known)
        self.assertIn("Pet MCP validation is not successful: v2", errors)

    def test_wrong_grid_and_metadata_version_are_reported(self):
        self.manifest["formats"]["v2"]["frames_per_row"][0] = 8
        self.save_manifest()
        self.change_json("v2/pet.json", lambda data: data.update(spriteVersionNumber=1))
        _, errors = VERIFY.verify_pet_manifest(self.root, self.known)
        self.assertIn("Pet format mismatch: v2/frames_per_row", errors)
        self.assertIn("Pet metadata mismatch: v2/spriteVersionNumber", errors)

    def test_metadata_cannot_reference_an_external_file(self):
        self.change_json("v2/pet.json", lambda data: data.update(
            spritesheetPath="../../../../outside.png"))
        _, errors = VERIFY.verify_pet_manifest(self.root, self.known)
        self.assertIn("Invalid pet path: v2/spritesheetPath", errors)

    def test_non_object_format_does_not_interrupt_validation(self):
        self.manifest["formats"]["v1"] = []
        self.save_manifest()
        stats, errors = VERIFY.verify_pet_manifest(self.root, self.known)
        self.assertIn("Invalid pet format: v1", errors)
        self.assertEqual(stats["pet_formats_metadata_checked"], 1)


if __name__ == "__main__":
    unittest.main()
