import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import traceback
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tts',ROOT/'skills/whale-tts/scripts/generate.py')
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
        self.assertEqual(json.loads(err)['error_code'],'dependency_missing')
        self.assertEqual(json.loads(err)['stage'],'dependency')

    def test_root_and_output_are_independent_of_package_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'任意角色目录'
            index=root/'assets/stickers/common/index.json'
            index.parent.mkdir(parents=True);index.write_text('[]')
            with patch.dict(os.environ,{'WHALE_CHAN_ROOT':'','WHALE_AUDIO_DIR':''}), \
                 patch.object(tts,'__file__',str(root/'skills/whale-tts/scripts/generate.py')):
                self.assertEqual(tts.resolve_root(),root)
                args=tts.build_parser().parse_args(['--text','test'])
                self.assertEqual(tts.output_dir(args),root/'output/audio')
            chosen=Path(tmp)/'发送目录'
            with patch.dict(os.environ,{'WHALE_AUDIO_DIR':str(Path(tmp)/'unused')}), \
                 patch.object(tts,'resolve_root') as resolve:
                args=tts.build_parser().parse_args(['--text','test','--output-dir',str(chosen)])
                self.assertEqual(tts.output_dir(args),chosen)
                resolve.assert_not_called()

    def test_utf8_file_and_custom_voice_parameters(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'朗读.txt';source.write_text('已经核对好了。',encoding='utf-8')
            def fake(command,**kwargs):
                self.assertEqual(command[0],'/fixture/edge-tts')
                self.assertEqual(command[-2:],['--file',str(source)])
                self.assertIn('--rate=-5%',command)
                self.assertIn('--pitch=-3Hz',command)
                Path(command[command.index('--write-media')+1]).write_bytes(b'ID3fixture')
                return subprocess.CompletedProcess(command,0)
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'), \
                 patch.object(tts.subprocess,'run',side_effect=fake):
                status,out,err=self.call(['--file',str(source),'--output-dir',tmp,
                                         '--voice','available-voice','--rate=-5%','--pitch=-3Hz'])
            self.assertEqual(status,0,err)
            result=json.loads(out)
            self.assertEqual((result['voice'],result['rate'],result['pitch']),
                             ('available-voice','-5%','-3Hz'))

    def test_invalid_input_before_service_call(self):
        with patch.object(tts.subprocess,'run') as run:
            status,out,err=self.call(['--text','test','--pitch','invalid'])
        self.assertEqual(status,2);run.assert_not_called();self.assertFalse(out)

    def test_cli_parse_failures_are_json_without_echoing_values(self):
        for extra in (['--timeout','PRIVATE_MARKER'],['--PRIVATE_MARKER']):
            with self.subTest(extra=extra):
                result=subprocess.run(
                    [tts.sys.executable,str(Path(tts.__file__)),'--text','正常短句',*extra],
                    capture_output=True,text=True,encoding='utf-8',check=False)
                self.assertEqual(result.returncode,2)
                self.assertFalse(result.stdout)
                self.assertNotIn('PRIVATE_MARKER',result.stderr)
                payload=json.loads(result.stderr)
                self.assertEqual((payload['error_code'],payload['stage']),('invalid_input','input'))

    def test_literal_option_text_survives_downstream_argument_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(command,**kwargs):
                # Simulate a CLI boundary with real argument parsing, no synthesis.
                parser=argparse.ArgumentParser()
                for option in ('voice','rate','volume','pitch','write-media','text'):
                    parser.add_argument('--'+option)
                parsed=parser.parse_args(command[1:])
                self.assertEqual(parsed.text,'--help')
                Path(parsed.write_media).write_bytes(b'ID3fixture')
                return subprocess.CompletedProcess(command,0)
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'), \
                 patch.object(tts.subprocess,'run',side_effect=fake):
                status,out,err=self.call(['--text=--help','--output-dir',tmp])
            self.assertEqual(status,0,err)
            self.assertTrue(json.loads(out)['ok'])

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
            self.assertEqual(set(result),{'ok','path','bytes','media_type','voice','pitch','rate','volume','provider'})
            self.assertFalse(list(Path(tmp).glob('*.part.mp3')))

    def test_service_failure_is_redacted_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.CompletedProcess([],3,stdout='private text',stderr='secret URL')
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'),patch.object(tts.subprocess,'run',return_value=result):
                status,out,err=self.call(['--text','test','--output-dir',tmp])
            self.assertEqual(status,2);self.assertFalse(out)
            self.assertNotIn('private',err);self.assertNotIn('secret',err)
            self.assertEqual(json.loads(err)['error_code'],'provider_error')
            self.assertFalse(list(Path(tmp).iterdir()))

    def test_provider_failure_reports_observed_kind_without_raw_log(self):
        cases = [
            ('edge_tts.exceptions.NoAudioReceived: no audio; private secret', 'no_audio_received'),
            ("aiohttp.client_exceptions.WSServerHandshakeError: 403, message='private secret', url='wss://secret'", 'http_403'),
            ("aiohttp.client_exceptions.ClientResponseError: 429, message='private secret'", 'http_429'),
            ('aiohttp.client_exceptions.ClientConnectorDNSError: private secret', 'network_error'),
            ('aiohttp.client_exceptions.ClientConnectorCertificateError: private secret', 'tls_error'),
            ('edge_tts.exceptions.UnexpectedResponse: private secret', 'protocol_error'),
            ('edge_tts.exceptions.WebSocketError: private secret', 'websocket_error'),
        ]
        for trace,code in cases:
            with self.subTest(code=code),tempfile.TemporaryDirectory() as tmp:
                result=subprocess.CompletedProcess([],1,stdout='private input',stderr=trace)
                with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'), \
                     patch.object(tts.subprocess,'run',return_value=result):
                    status,out,err=self.call(['--text','test','--output-dir',tmp])
                payload=json.loads(err)
                self.assertEqual(status,2);self.assertFalse(out)
                self.assertEqual((payload['error_code'],payload['stage']),(code,'synthesis'))
                self.assertNotIn('private',err);self.assertNotIn('secret',err)
                self.assertFalse(list(Path(tmp).iterdir()))

    def test_traceback_source_and_exception_message_are_not_failure_kind(self):
        traces = [
            '  raise NoAudioReceived("private")\nRuntimeError: private secret 403',
            "RuntimeError: WSServerHandshakeError: 403, message='private secret'",
            "aiohttp.client_exceptions.WSServerHandshakeError: 500, message='private secret 403'",
        ]
        for trace in traces:
            with self.subTest(trace=trace),tempfile.TemporaryDirectory() as tmp:
                result=subprocess.CompletedProcess([],1,stderr=trace)
                with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'), \
                     patch.object(tts.subprocess,'run',return_value=result):
                    status,out,err=self.call(['--text','test','--output-dir',tmp])
                self.assertEqual(status,2);self.assertFalse(out)
                self.assertNotIn(json.loads(err)['error_code'],('http_403','no_audio_received'))
                self.assertNotIn('private',err);self.assertNotIn('secret',err)

    def test_multiline_exception_text_cannot_supply_failure_kind(self):
        messages = [
            'request text:\nNoAudioReceived: private secret',
            'request text:\naiohttp.client_exceptions.WSServerHandshakeError: 403, private secret',
            'request text:\nTraceback (most recent call last):\n'
            '  File "quoted.txt", line 1, in <module>\nNoAudioReceived: private secret',
        ]
        for message in messages:
            # Format a real exception: its unindented continuation is user text,
            # even when that continuation looks exactly like another exception.
            try:
                raise RuntimeError(message)
            except RuntimeError:
                trace = traceback.format_exc()
            with self.subTest(message=message), tempfile.TemporaryDirectory() as tmp:
                result = subprocess.CompletedProcess([], 1, stderr=trace)
                with patch.object(tts.shutil, 'which', return_value='/fixture/edge-tts'), \
                     patch.object(tts.subprocess, 'run', return_value=result):
                    status, out, err = self.call(['--text', 'test', '--output-dir', tmp])
                payload = json.loads(err)
                self.assertEqual(status, 2); self.assertFalse(out)
                self.assertEqual((payload['error_code'], payload['stage']),
                                 ('provider_error', 'synthesis'))
                self.assertNotIn('private', err); self.assertNotIn('secret', err)
                self.assertFalse(list(Path(tmp).iterdir()))

    def test_real_traceback_header_precedes_message_continuation(self):
        error_type = type('WSServerHandshakeError', (Exception,), {})
        try:
            raise error_type('403, private secret\nRuntimeError: quoted text')
        except Exception:
            trace = traceback.format_exc()
        failure = tts.provider_failure(trace, 1)
        self.assertEqual(failure.code, 'http_403')
        self.assertNotIn('private', str(failure)); self.assertNotIn('secret', str(failure))

    def test_timeout_without_exception_message_is_classified(self):
        try:
            raise TimeoutError
        except TimeoutError:
            trace = traceback.format_exc()
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.CompletedProcess([], 1, stderr=trace)
            with patch.object(tts.shutil, 'which', return_value='/fixture/edge-tts'), \
                 patch.object(tts.subprocess, 'run', return_value=result):
                status, out, err = self.call(['--text', 'test', '--output-dir', tmp])
            payload = json.loads(err)
            self.assertEqual(status, 2); self.assertFalse(out)
            self.assertEqual((payload['error_code'], payload['stage']),
                             ('timeout', 'synthesis'))
            self.assertFalse(list(Path(tmp).iterdir()))

    def test_invalid_audio_is_not_delivered(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(command,**kwargs):
                Path(command[command.index('--write-media')+1]).write_bytes(b'not audio')
                return subprocess.CompletedProcess(command,0)
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'),patch.object(tts.subprocess,'run',side_effect=fake):
                status,out,err=self.call(['--text','test','--output-dir',tmp])
            self.assertEqual(status,2);self.assertFalse(out);self.assertFalse(list(Path(tmp).iterdir()))
            self.assertEqual((json.loads(err)['error_code'],json.loads(err)['stage']),
                             ('invalid_audio','validation'))

    def test_timeout_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(tts.shutil,'which',return_value='/fixture/edge-tts'),patch.object(tts.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',1)):
                status,out,err=self.call(['--text','test','--output-dir',tmp])
            self.assertEqual(status,2);self.assertFalse(out);self.assertFalse(list(Path(tmp).iterdir()))
            self.assertEqual((json.loads(err)['error_code'],json.loads(err)['stage']),
                             ('timeout','synthesis'))

if __name__=='__main__':unittest.main()
