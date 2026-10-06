import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pet_asset", ROOT / "scripts/pet_asset.py")
pet = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pet)


@unittest.skipUnless(Image is not None, "optional Pillow dependency is not installed")
class PetTests(unittest.TestCase):
    def fixture(self, path, identical=False):
        # Synthetic boundary fixture only, never exported as a character asset.
        spec = pet.profile()
        atlas = Image.new("RGBA", (1536, 1872), (0, 0, 0, 0))
        draw = ImageDraw.Draw(atlas)
        for state in spec["states"]:
            for column in range(state["frames"]):
                x, y = column * 192, state["row"] * 208
                delta = 0 if identical else column
                draw.rectangle((x + 60, y + 60, x + 120 + delta, y + 150), fill=(40, 90, 150, 255))
        atlas.save(path)

    def test_structural_pass_never_claims_semantics_or_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.png"
            self.fixture(path)
            result = pet.validate(path)
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["used_cells_expected"], 57)
            self.assertFalse(result["visual_semantics_verified"])
            self.assertFalse(result["host_import_verified"])

    def test_unused_cells_must_be_completely_transparent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.png"
            self.fixture(path)
            with Image.open(path) as source:
                image = source.convert("RGBA")
            image.putpixel((7 * 192 + 50, 50), (1, 2, 3, 1))
            image.save(path)
            self.assertIn("unused_cell_not_transparent:idle:7", pet.validate(path)["errors"])

    def test_whole_row_repeated_frames_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.png"
            self.fixture(path, identical=True)
            self.assertIn("state_has_no_frame_variation:idle", pet.validate(path)["errors"])

    def test_used_cell_missing_and_margin_clipping_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.png"
            self.fixture(path)
            with Image.open(path) as source:
                image = source.convert("RGBA")
            image.paste((0, 0, 0, 0), (0, 0, 192, 208))
            image.putpixel((192, 80), (20, 20, 20, 255))
            image.save(path)
            errors = pet.validate(path)["errors"]
            self.assertIn("used_cell_empty:idle:0", errors)
            self.assertIn("subject_touches_cell_margin:idle:1", errors)

    def test_11row_input_is_not_silently_cropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.png"
            Image.new("RGBA", (1536, 2288)).save(path)
            with self.assertRaisesRegex(ValueError, "atlas_dimensions"):
                pet.validate(path)

    def test_package_requires_visual_attestation_and_new_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, output = Path(tmp) / "fixture.png", Path(tmp) / "candidate"
            self.fixture(path)
            with self.assertRaisesRegex(ValueError, "visual_review_confirmation"):
                pet.package(path, output, "test-pet", "fixture", False)
            self.assertFalse(output.exists())
            receipt = pet.package(path, output, "test-pet", "fixture", True)
            self.assertTrue(receipt["structural_validation_passed"])
            self.assertFalse(receipt["host_import_verified"])
            self.assertIn("caller_attested", receipt["visual_review"])
            metadata = json.loads((output / "pet.json").read_text(encoding="utf-8"))
            self.assertEqual(set(metadata), {"id", "displayName", "description", "spritesheetPath"})
            self.assertNotIn("spriteVersionNumber", metadata)
            self.assertIn("prefers-reduced-motion", (output / "preview.html").read_text(encoding="utf-8"))
            with self.assertRaisesRegex(ValueError, "already_exists"):
                pet.package(path, output, "test-pet", "fixture", True)


class PetProfileTests(unittest.TestCase):
    def test_protocol_counts_and_durations_are_consistent(self):
        profile = pet.profile()
        self.assertEqual(len(profile["states"]), 9)
        self.assertEqual([x["row"] for x in profile["states"]], list(range(9)))
        self.assertEqual(profile["width"], profile["columns"] * profile["cell_width"])
        self.assertEqual(profile["height"], profile["rows"] * profile["cell_height"])
        for state in profile["states"]:
            self.assertEqual(state["frames"], len(state["durations_ms"]))
            self.assertTrue(all(type(ms) is int and ms > 0 for ms in state["durations_ms"]))
        self.assertFalse(profile["candidate_artwork_present"])
        self.assertFalse(profile["dot_import_tested"])


if __name__ == "__main__":
    unittest.main()
