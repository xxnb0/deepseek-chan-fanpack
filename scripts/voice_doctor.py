#!/usr/bin/env python3
"""Offline environment inspection; optional bounded MP3 decode, never speech synthesis."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def environment() -> dict:
    try:
        version = importlib.metadata.version("edge-tts")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {
        "python_version": platform.python_version(),
        "edge_module_available": importlib.util.find_spec("edge_tts") is not None,
        "edge_module_version": version,
        "edge_cli_available": shutil.which("edge-tts") is not None,
        "cli_python_alignment": "not_verified",
        "ffprobe_available": shutil.which("ffprobe") is not None,
        "ffmpeg_available": shutil.which("ffmpeg") is not None
    }


def inspect_audio(path: Path, decode: bool = False, timeout: float = 20) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("audio_must_be_regular_local_file")
    if not 0 < path.stat().st_size <= 100 * 1024 * 1024:
        raise ValueError("audio_size_out_of_bounds")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        head = stream.read(3)
        if not (head == b"ID3" or (len(head) > 1 and head[0] == 255 and head[1] & 224 == 224)):
            raise ValueError("mp3_header_missing")
        digest.update(head)
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    result = {"bytes": path.stat().st_size, "sha256": digest.hexdigest(),
              "mp3_header_present": True, "decoded": False,
              "subjective_audition": "not_run", "delivery": "not_run"}
    if not decode:
        return result
    probe, ffmpeg = shutil.which("ffprobe"), shutil.which("ffmpeg")
    if not probe or not ffmpeg:
        raise ValueError("decode_tools_missing")
    # Force an MP3 demuxer and file-only protocols, even for hostile mislabeled input.
    source = str(path.resolve(strict=True))
    probe_run = subprocess.run(
        [probe, "-v", "error", "-protocol_whitelist", "file,pipe", "-f", "mp3",
         "-show_entries", "format=duration:stream=codec_name,sample_rate,channels",
         "-of", "json", source], capture_output=True, text=True, timeout=timeout, check=False)
    if probe_run.returncode:
        raise ValueError("audio_probe_failed")
    data = json.loads(probe_run.stdout)
    duration = float(data.get("format", {}).get("duration", 0))
    streams = data.get("streams", [])
    if not math.isfinite(duration) or duration <= 0 or not streams:
        raise ValueError("audio_probe_has_no_valid_stream")
    decode_run = subprocess.run(
        [ffmpeg, "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe",
         "-f", "mp3", "-i", source, "-f", "null", "-"],
        capture_output=True, text=True, timeout=timeout, check=False)
    if decode_run.returncode:
        raise ValueError("full_audio_decode_failed")
    result.update({"decoded": True, "duration_seconds": duration,
                   "streams": [{key: stream[key] for key in ("codec_name", "sample_rate", "channels")
                                if key in stream} for stream in streams]})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--decode", action="store_true")
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args(argv)
    if args.decode and not args.audio:
        parser.error("--decode requires --audio")
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 120:
        parser.error("--timeout must be finite, positive and no more than 120 seconds")
    result = {"ok": True, "inspection_completed": False, "network_requested": False,
              "online_synthesis": "not_run", "realtime_voice_replacement": "not_tested",
              "environment": environment(), "audio": None}
    try:
        if args.audio:
            result["audio"] = inspect_audio(args.audio.expanduser(), args.decode, args.timeout)
        result["inspection_completed"] = True
    except subprocess.TimeoutExpired:
        result.update({"ok": False, "error_code": "decode_timeout"})
    except (OSError, ValueError, KeyError, TypeError) as exc:
        known = {"audio_must_be_regular_local_file", "audio_size_out_of_bounds",
                 "mp3_header_missing", "decode_tools_missing", "audio_probe_failed",
                 "audio_probe_has_no_valid_stream", "full_audio_decode_failed"}
        code = str(exc) if type(exc) is ValueError and str(exc) in known else "audio_inspection_failed"
        result.update({"ok": False, "error_code": code})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
