"""离线标准库测试；临时素材仅在系统临时目录，不修改正式资产。"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "scripts/pick.py"
spec = importlib.util.spec_from_file_location("portable_pick", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PickTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="whale-pick-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "包 数据" / "deepseek-chan"
        self.common = self.root / "assets/stickers/common"
        self.common.mkdir(parents=True)
        self.items, self.variants = [], []
        for name, source, meaning, transparent in (
            ("01_正式.png", "ZIP-01", "正式开场", False),
            ("新Q_01_问好.png", "SUNBURST-01", "问好开场", True),
            ("新Q_04_交付 #.png", "SUNBURST-04", "完成交付", True),
        ):
            content = name.encode("utf-8")
            (self.common / name).write_bytes(content)
            sha = hashlib.sha256(content).hexdigest()
            self.items.append(dict(file=name, source_id=source, meaning=meaning,
                                   usage="必须实际符合场景", text_note="文字限制", sha256=sha, bytes=len(content)))
            self.variants.append(dict(file=name, background="transparent" if transparent else "opaque",
                                      has_alpha=transparent, alpha_min=0 if transparent else 255,
                                      alpha_max=255, sha256=sha))
        self.save()
        env = patch.dict(os.environ, {"WHALE_CHAN_ROOT": ""})
        env.start()
        self.addCleanup(env.stop)

    def save(self):
        (self.common / "index.json").write_text(json.dumps(self.items), encoding="utf-8")
        (self.common / "variants.json").write_text(json.dumps(self.variants), encoding="utf-8")

    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = mod.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def test_list_hash_and_notes(self):
        code, out, _ = self.call("list")
        self.assertEqual(code, 0)
        entries = json.loads(out)["entries"]
        self.assertEqual(len(entries), 3)
        self.assertTrue(all(x["sha256_verified"] for x in entries))
        self.assertEqual(entries[0]["text_note"], "文字限制")
        self.assertIn("usage", entries[0])

    def test_pick_exact_and_path(self):
        for query in ("SUNBURST-04", "新Q_04_交付 #", "新Q_04_交付 #.png", "完成交付"):
            code, out, _ = self.call("pick", query, "--format", "path")
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), str(self.common / self.items[2]["file"]))

    def test_ambiguous_and_missing_are_not_success(self):
        for query in ("开场", "不存在", " "):
            code, out, err = self.call("pick", query)
            self.assertEqual(code, 2)
            self.assertEqual(out, "")
            self.assertFalse(json.loads(err)["ok"])

    def test_numeric_does_not_fall_back_to_new_q(self):
        self.assertEqual(self.call("pick", "1")[0], 0)
        code, out, _ = self.call("pick", "1", "--transparent-only")
        self.assertEqual((code, out), (2, ""))

    def test_transparent_filter_preserves_semantics(self):
        code, out, _ = self.call("list", "--transparent-only")
        self.assertEqual(code, 0)
        entries = json.loads(out)["entries"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["usage"], "必须实际符合场景")
        self.assertEqual(self.call("pick", "ZIP-01", "--transparent-only")[0], 2)

    def test_missing_or_incomplete_metadata_fails_closed(self):
        (self.common / "variants.json").unlink()
        self.assertEqual(self.call("list")[0], 0)
        self.assertEqual(self.call("list", "--transparent-only")[0], 2)
        self.variants.pop()
        self.save()
        self.assertEqual(self.call("list", "--transparent-only")[0], 2)

    def test_fake_alpha_rejected(self):
        self.variants[0].update(background="transparent", has_alpha=True, alpha_min=255)
        self.save()
        self.assertEqual(self.call("list", "--transparent-only")[0], 2)

    def test_variant_hash_mismatch(self):
        self.variants[0]["sha256"] = "0" * 64
        self.save()
        self.assertEqual(self.call("list")[0], 2)

    def test_actual_hash_mismatch_outputs_nothing(self):
        (self.common / self.items[0]["file"]).write_bytes(b"changed")
        code, out, _ = self.call("pick", "ZIP-01")
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(self.call("list")[0], 2)

    def test_missing_file(self):
        (self.common / self.items[0]["file"]).unlink()
        self.assertEqual(self.call("pick", "ZIP-01")[0], 2)

    def test_filename_traversal(self):
        for name in ("../outside.png", "/tmp/a", "C:\\outside.png"):
            self.items[0]["file"] = name
            self.save()
            self.assertEqual(self.call("list")[0], 2)

    def test_symlink_escape(self):
        outside = Path(self.temp.name) / "outside.png"
        outside.write_bytes(b"outside")
        image = self.common / self.items[0]["file"]
        image.unlink()
        image.symlink_to(outside)
        self.assertEqual(self.call("pick", "ZIP-01")[0], 2)

    def test_duplicate_index(self):
        self.items.append(self.items[0].copy())
        self.save()
        self.assertEqual(self.call("list")[0], 2)

    def test_complete_file_uri_encoding_and_minis_rejection(self):
        code, out, _ = self.call("pick", "SUNBURST-04", "--format", "markdown")
        self.assertEqual(code, 0)
        self.assertIn("file:///", out)
        self.assertIn("%E5%8C%85%20%E6%95%B0%E6%8D%AE", out)
        self.assertIn("%20%23.png", out)
        self.assertEqual(self.call("pick", "SUNBURST-04", "--format", "minis")[0], 2)

    def test_http_user_base(self):
        code, out, _ = self.call("pick", "SUNBURST-04", "--format", "markdown",
                                 "--url-base", "https://media.example.org/鲸鱼 图/")
        self.assertEqual(code, 0)
        self.assertIn("https://media.example.org/%E9%B2%B8%E9%B1%BC%20%E5%9B%BE/", out)
        self.assertNotIn("file:///", out)

    def test_http_credentials_rejected_without_echo(self):
        code, out, err = self.call("pick", "ZIP-01", "--url-base",
                                   "https://u:secret@example.org/common/")
        self.assertEqual((code, out), (2, ""))
        self.assertNotIn("secret", err)

    def test_root_precedence_and_sibling_discovery(self):
        with patch.dict(os.environ, {"WHALE_CHAN_ROOT": str(self.root)}):
            self.assertEqual(mod.resolve_root(), self.root)
            with self.assertRaises(ValueError):
                mod.resolve_root(str(self.root / "missing"))
        with patch.object(mod, "__file__", str(self.root / "skills/whale-stickers/scripts/pick.py")):
            self.assertEqual(mod.resolve_root(), self.root)
        workspace = self.root.parent
        with patch.object(mod, "__file__", str(workspace / "skills/whale-stickers/scripts/pick.py")):
            self.assertEqual(mod.resolve_root(), self.root)


if __name__ == "__main__":
    unittest.main()
