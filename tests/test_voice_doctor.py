import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("voice_doctor", ROOT / "scripts/voice_doctor.py")
doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctor)


class VoiceDoctorTests(unittest.TestCase):
    def call(self, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = doctor.main(args)
        return status, json.loads(output.getvalue())

    def test_default_does_not_spawn_or_synthesize(self):
        with patch.object(doctor.subprocess, "run") as run:
            status, result = self.call([])
        self.assertEqual(status, 0)
        run.assert_not_called()
        self.assertFalse(result["network_requested"])
        self.assertEqual(result["online_synthesis"], "not_run")
        self.assertEqual(result["realtime_voice_replacement"], "not_tested")

    def test_header_is_not_decode_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.mp3"
            path.write_bytes(b"ID3not-really-an-audio-fixture")
            with patch.object(doctor.subprocess, "run") as run:
                result = doctor.inspect_audio(path)
            run.assert_not_called()
            self.assertTrue(result["mp3_header_present"])
            self.assertFalse(result["decoded"])

    def test_invalid_header_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.mp3"
            path.write_bytes(b"not mp3")
            with self.assertRaisesRegex(ValueError, "mp3_header_missing"):
                doctor.inspect_audio(path)

    def test_successful_decode_preserves_no_delivery_claim(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.mp3"
            path.write_bytes(b"ID3test")
            probe = subprocess.CompletedProcess([], 0, json.dumps({"format":{"duration":"1.2"},
                "streams":[{"codec_name":"mp3","sample_rate":"24000","channels":1}]}), "")
            with patch.object(doctor.shutil, "which", side_effect=lambda name: "/fixture/" + name), \
                 patch.object(doctor.subprocess, "run", side_effect=[probe, subprocess.CompletedProcess([], 0, "", "")]) as run:
                result = doctor.inspect_audio(path, True)
            self.assertTrue(result["decoded"])
            self.assertEqual(result["delivery"], "not_run")
            self.assertEqual(result["subjective_audition"], "not_run")
            for call in run.call_args_list:
                args = call.args[0]
                self.assertIn("file,pipe", args)
                self.assertIn("mp3", args)

    def test_provider_errors_are_not_echoed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.mp3"
            path.write_bytes(b"ID3test")
            with patch.object(doctor.shutil, "which", return_value="/fixture/tool"), \
                 patch.object(doctor.subprocess, "run", return_value=subprocess.CompletedProcess([], 3, "private text", "secret URL")):
                status, result = self.call(["--audio", str(path), "--decode"])
            self.assertEqual(status, 2)
            self.assertEqual(result["error_code"], "audio_probe_failed")
            self.assertNotIn("secret", json.dumps(result))
            self.assertNotIn("private", json.dumps(result))

    def test_timeout_is_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.mp3"
            path.write_bytes(b"ID3test")
            with patch.object(doctor.shutil, "which", return_value="/fixture/tool"), \
                 patch.object(doctor.subprocess, "run", side_effect=subprocess.TimeoutExpired("fixture", 1)):
                status, result = self.call(["--audio", str(path), "--decode"])
            self.assertEqual(status, 2)
            self.assertEqual(result["error_code"], "decode_timeout")


if __name__ == "__main__":
    unittest.main()
