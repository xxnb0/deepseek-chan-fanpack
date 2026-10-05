import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify_pack',ROOT/'scripts/verify.py')
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)

class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'pack'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        # Deliberately sparse fixture: never needs downloading any media.
        for p in self.root.rglob('*'):
            if p.is_file() and p.suffix.lower() in verify.MEDIA:p.unlink()
        manifest=json.loads((self.root/'manifest.json').read_text())
        for item in manifest['files']:
            p=self.root/item['path']
            if p.is_file():item.update(bytes=p.stat().st_size,sha256=verify.sha(p))
        (self.root/'manifest.json').write_text(json.dumps(manifest))

    def tearDown(self):self.tmp.cleanup()

    def test_metadata_reports_every_skipped_image(self):
        result=verify.verify(self.root,metadata_only=True)
        self.assertTrue(result['ok'],result['errors'])
        self.assertFalse(result['full_media_verification'])
        self.assertEqual(len(result['media_files_not_byte_verified']),36)
        self.assertEqual(result['media_files_byte_verified'],0)

    def test_full_mode_rejects_sparse_checkout(self):
        result=verify.verify(self.root)
        self.assertFalse(result['ok'])
        self.assertTrue(any('Missing: assets/' in e for e in result['errors']))

    def test_metadata_does_not_hide_broken_document_links(self):
        p=self.root/'README.md';p.write_text(p.read_text()+'\n[bad](not-a-real-doc.md)\n<img src="missing-image.png">\n')
        result=verify.verify(self.root,metadata_only=True)
        self.assertFalse(result['ok'])
        self.assertTrue(any('Broken document link' in e for e in result['errors']))

    def test_existing_wrong_media_is_not_skipped(self):
        p=self.root/'assets/reference/character-fullbody.webp';p.write_bytes(b'invalid fixture')
        result=verify.verify(self.root,metadata_only=True)
        self.assertFalse(result['ok'])
        self.assertTrue(any('Checksum mismatch: assets/reference/' in e for e in result['errors']))

if __name__=='__main__':unittest.main()
