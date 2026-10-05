#!/usr/bin/env python3
"""Generate online Edge TTS audio directly into Minis chat attachments."""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ATTACHMENTS = Path('/var/minis/attachments')
# Recommended character match: lively Mandarin voice without a regional accent.
DEFAULT_VOICE = 'zh-CN-XiaoyiNeural'


def safe_name(value: str) -> str:
    value = re.sub(r'[^A-Za-z0-9_-]+', '-', value).strip('-_')
    return (value[:48] or 'speech')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--text', help='Text to synthesize')
    source.add_argument('--file', help='UTF-8 text file to synthesize')
    parser.add_argument('--voice', default=DEFAULT_VOICE)
    parser.add_argument('--rate', default='+0%')
    parser.add_argument('--volume', default='+0%')
    parser.add_argument('--pitch', default='+22Hz')
    parser.add_argument('--name', default='speech', help='Optional filename prefix')
    args = parser.parse_args()

    if not ATTACHMENTS.is_dir():
        print(f'Error: Minis attachments directory missing: {ATTACHMENTS}', file=sys.stderr)
        return 2
    if not shutil_which('edge-tts'):
        print('Error: edge-tts is not installed in this runtime.', file=sys.stderr)
        return 2

    prefix = safe_name(args.name)
    output = ATTACHMENTS / f'{prefix}-{time.strftime("%Y%m%d-%H%M%S")}-{time.time_ns() % 1000000:06d}.mp3'
    command = [
        'edge-tts', '--voice', args.voice, '--rate', args.rate,
        '--volume', args.volume, '--pitch', args.pitch,
        '--write-media', str(output),
    ]
    command += ['--text', args.text] if args.text is not None else ['--file', args.file]
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=False)
    except OSError as exc:
        print(f'Error starting edge-tts: {exc}', file=sys.stderr)
        return 2
    if result.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
        output.unlink(missing_ok=True)
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        print('Error: TTS did not produce a valid audio file.', file=sys.stderr)
        return result.returncode or 1

    print(f'file={output}')
    print(f'minis_url=minis://attachments/{output.name}')
    print(f'bytes={output.stat().st_size}')
    return 0


def shutil_which(program: str):
    import shutil
    return shutil.which(program)


if __name__ == '__main__':
    raise SystemExit(main())
