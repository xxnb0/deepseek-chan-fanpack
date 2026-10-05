import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tts',ROOT/'skills/minis-tts/scripts/generate.py')
tts=importlib.util.module_from_spec(spec);spec.loader.exec_module(tts)

class TtsTests(unittest.TestCase):
    def call(self,args):
        out,err=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            status=tts.main(args)
        return status,out.getvalue(),err.getvalue()

    def test_reference_defaults_and_overrides(self):
        a=tts.build_parser().parse_args(['--text','test'])
        self.assertEqual((a.voice,a.pitch,a.rate),('zh-CN-XiaoyiNeural','+22Hz','+0%'))
        a=tts.build_parser().parse_args(['--text','test','--voice','host-choice','--pitch=-3Hz','--rate=-5%'])
        self.assertEqual((a.voice,a.pitch,a.rate),('host-choice','-3Hz','-5%'))

    def test_missing_dependency_has_no_success(self):
        with patch.object(tts.shutil,'which',return_value=None):
            status,out,err=self.call(['--text','test'])
        self.assertEqual(status,2);self.assertFalse(out);self.assertFalse(json.loads(err)['ok'])

    def test_invalid_input_before_service_call(self):
        with patch.object(tts.subprocess,'run') as run:
            status,out,err=self.call(['--text','test','--pitch','invalid'])
        self.assertEqual(status,2);run.assert_not_called();self.assertFalse(out)

    def test_mock_success_produces_file_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(command,**kwargs):
                Path(command[command.index('--write-media')+1]).write_bytes(b'ID3test-fixture')
                return subprocess.CompletedProcess(command,0)
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'),patch.object(tts.subprocess,'run',side_effect=fake):
                status,out,err=self.call(['--text','test','--output-dir',tmp,'--name','../../reply'])
            self.assertEqual(status,0,err)
            result=json.loads(out);p=Path(result['path'])
            self.assertEqual(p.parent,Path(tmp));self.assertTrue(p.is_file())
            self.assertEqual(result['provider'],'edge-tts-online')
            self.assertNotIn('minis_url',result)
            self.assertFalse(list(Path(tmp).glob('*.part.mp3')))

    def test_service_failure_is_redacted_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.CompletedProcess([],3,stdout='private text',stderr='secret URL')
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'),patch.object(tts.subprocess,'run',return_value=result):
                status,out,err=self.call(['--text','test','--output-dir',tmp])
            self.assertEqual(status,2);self.assertFalse(out)
            self.assertNotIn('private',err);self.assertNotIn('secret',err)
            self.assertFalse(list(Path(tmp).iterdir()))

    def test_invalid_audio_is_not_delivered(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(command,**kwargs):
                Path(command[command.index('--write-media')+1]).write_bytes(b'not audio')
                return subprocess.CompletedProcess(command,0)
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'),patch.object(tts.subprocess,'run',side_effect=fake):
                status,out,err=self.call(['--text','test','--output-dir',tmp])
            self.assertEqual(status,2);self.assertFalse(out);self.assertFalse(list(Path(tmp).iterdir()))

    def test_timeout_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'),patch.object(tts.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',1)):
                status,out,err=self.call(['--text','test','--output-dir',tmp])
            self.assertEqual(status,2);self.assertFalse(out);self.assertFalse(list(Path(tmp).iterdir()))

if __name__=='__main__':unittest.main()
