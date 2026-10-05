#!/usr/bin/env python3
"""调用在线 edge-tts 生成 MP3；默认输出 JSON，不假定聊天前端能力。"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_VOICE = "zh-CN-XiaoyiNeural"
DEFAULT_PITCH = "+22Hz"
DEFAULT_RATE = "+0%"


def resolve_root(explicit=None):
    selected = explicit or os.environ.get("WHALE_CHAN_ROOT")
    if selected:
        root = Path(selected).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("指定包数据目录不存在")
        return root
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "assets/stickers/common/index.json").is_file():
            return ancestor.resolve()
    raise ValueError("找不到包数据目录；请指定 --root、--output-dir 或 WHALE_AUDIO_DIR")


def output_dir(args):
    selected = args.output_dir or os.environ.get("WHALE_AUDIO_DIR")
    directory = (Path(selected).expanduser().resolve() if selected else
                 resolve_root(args.root) / "output/audio")
    directory.mkdir(parents=True, exist_ok=True)
    return directory.resolve(strict=True)



def safe_name(value):
    clean = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-_")
    return clean[:48] or "speech"


def validate_audio(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("edge-tts 未生成非空 MP3")
    with path.open("rb") as handle:
        head = handle.read(3)
    if not (head == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)):
        raise ValueError("输出内容没有 MP3/ID3 标记，不能作为有效语音交付")
    return path.stat().st_size


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="朗读文字，不能全空白")
    source.add_argument("--file", help="UTF-8 文本文件，与 --text 互斥")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="声线 ID，默认 %(default)s")
    parser.add_argument("--pitch", default=DEFAULT_PITCH, help="音高，默认 %(default)s；负值用 --pitch=-3Hz")
    parser.add_argument("--rate", default=DEFAULT_RATE, help="语速，默认 %(default)s；负值用 --rate=-5%%")
    parser.add_argument("--volume", default="+0%", help="音量，默认 %(default)s")
    parser.add_argument("--name", default="speech", help="安全文件名前缀；实际文件名含时间和随机 ID")
    parser.add_argument("--output-dir", help="输出目录；优先于 WHALE_AUDIO_DIR")
    parser.add_argument("--root", help="包数据目录；无输出目录时使用其 output/audio")
    parser.add_argument("--timeout", type=float, default=120, help="在线调用超时秒数，默认 %(default)s")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    temporary = None
    try:
        text_file = Path(args.file).expanduser().resolve(strict=True) if args.file else None
        text = text_file.read_text(encoding="utf-8") if text_file else args.text
        if not text or not text.strip():
            raise ValueError("没有可朗读的非空文字")
        if not args.voice.strip():
            raise ValueError("声线 ID 不能为空")
        for key, pattern in (("rate", r"[+-]\d+%"), ("volume", r"[+-]\d+%"),
                             ("pitch", r"[+-]\d+Hz")):
            if not re.fullmatch(pattern, getattr(args, key)):
                raise ValueError(key + " 格式无效；需带正负号及单位")
        if not 0 < args.timeout <= 3600:
            raise ValueError("--timeout 必须大于零且不超过 3600 秒")
        executable = shutil.which("edge-tts")
        if not executable:
            raise ValueError("未安装 edge-tts；请先安装 requirements-tts.txt")
        directory = output_dir(args)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = directory / f"{safe_name(args.name)}-{stamp}-{uuid.uuid4().hex[:12]}.mp3"
        descriptor, filename = tempfile.mkstemp(prefix=".tts-", suffix=".part.mp3", dir=directory)
        os.close(descriptor)
        temporary = Path(filename)
        command = [executable, "--voice", args.voice, "--rate=" + args.rate,
                   "--volume=" + args.volume, "--pitch=" + args.pitch,
                   "--write-media", str(temporary)]
        command += ["--file", str(text_file)] if text_file else ["--text", text]
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=args.timeout, check=False)
        if result.returncode:
            # 不把服务端日志、请求 URL 或运行环境中的凭据回显到聊天/仓库。
            raise ValueError(f"edge-tts 调用失败（退出码 {result.returncode}）；请检查网络及服务可用性")
        size = validate_audio(temporary)
        os.replace(temporary, output)
        temporary = None
        payload = {"ok": True, "path": str(output), "bytes": size, "media_type": "audio/mpeg",
                   "voice": args.voice, "pitch": args.pitch, "rate": args.rate,
                   "volume": args.volume, "provider": "edge-tts-online"}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "error": "edge-tts 调用超时；未交付音频"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
