#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
INSTALL=ROOT/'scripts/install.py'

class InstallTests(unittest.TestCase):
    def run_install(self,target,path,*extra,expected=0):
        r=subprocess.run([sys.executable,str(INSTALL),'--target',target,'--workspace',str(path),*extra],capture_output=True,text=True)
        self.assertEqual(r.returncode,expected,r.stdout+r.stderr)
        return r

    def test_dry_run_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'not-created'
            self.run_install('generic',path,'--dry-run')
            self.assertFalse(path.exists())

    def test_layouts_idempotence_and_picker(self):
        with tempfile.TemporaryDirectory() as tmp:
            for target in ('generic','openclaw','hermes','cursor'):
                path=Path(tmp)/target
                self.run_install(target,path)
                prefix=path/('.cursor/skills' if target=='cursor' else 'skills')
                pick=prefix/'whale-stickers/scripts/pick.py'
                result=subprocess.run([sys.executable,str(pick),'pick','新Q_04','--format','json'],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                data=json.loads(result.stdout)
                self.assertTrue(data['sticker']['sha256_verified'])
                self.assertTrue(data['root'].startswith(str(path)))
                before={p.relative_to(path).as_posix():p.read_bytes() for p in path.glob('*.md')}
                self.run_install(target,path)
                after={p.relative_to(path).as_posix():p.read_bytes() for p in path.glob('*.md')}
                self.assertEqual(before,after)
                self.assertFalse((path/'deepseek-chan/archive').exists())

    def test_conflict_refused_backup_and_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            (path/'SOUL.md').write_text('Existing persona')
            (path/'AGENTS.md').write_text('Keep host operations')
            self.run_install('openclaw',path,expected=2)
            self.assertEqual((path/'SOUL.md').read_text(),'Existing persona')
            self.run_install('openclaw',path,'--dry-run')
            self.run_install('openclaw',path,'--replace-persona')
            self.assertIn('Keep host operations',(path/'AGENTS.md').read_text())
            backup=list((path/'.deepseek-chan-backups').glob('*/SOUL.md'))
            self.assertEqual(len(backup),1)
            self.assertEqual(backup[0].read_text(),'Existing persona')

    def test_external_symlink_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'host';path.mkdir()
            outside=Path(tmp)/'outside';outside.mkdir()
            (path/'skills').symlink_to(outside,target_is_directory=True)
            self.run_install('generic',path,expected=2)
            self.assertFalse((outside/'whale-stickers').exists())

if __name__=='__main__': unittest.main()
