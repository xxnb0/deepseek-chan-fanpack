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


class TtsFailure(ValueError):
    """A safe public error, never a raw provider traceback."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message):
        # argparse's raw message can include requested speech or other input.
        raise TtsFailure("invalid_input", "命令参数无效；使用 --help 查看必填项与参数格式")


def exception_header(stderr):
    """Read a single-line error or the header after a standard traceback's frames."""
    lines = [line for line in (stderr or "").splitlines() if line.strip()]
    if len(lines) == 1:
        candidate = lines[0]
    else:
        marker = "Traceback (most recent call last):"
        # Chained/grouped tracebacks or a quoted second traceback are ambiguous
        # in plain stderr. Do not search them for a more convenient error type.
        if not lines or lines[0] != marker or lines.count(marker) != 1:
            return "", ""
        candidate = ""
        seen_frame = False
        for line in lines[1:]:
            if re.fullmatch(r'  File ".+", line \d+(?:, in .+)?', line):
                seen_frame = True
                continue
            if not seen_frame:
                return "", ""
            if line.startswith("    ") or re.fullmatch(
                    r"  \[Previous line repeated \d+ more times\]", line):
                continue
            # This first unindented line follows the frames. Later lines belong
            # to its possibly multiline message or notes, never another type.
            candidate = line
            break
    match = re.fullmatch(
        r"(?:[A-Za-z_]\w*\.)*([A-Za-z_]\w*)(?::[ \t]*(.*))?", candidate)
    return (match.group(1), match.group(2) or "") if match else ("", "")


def provider_failure(stderr, returncode):
    """Classify the parsed exception header without exposing provider text."""
    kind, detail = exception_header(stderr)
    code = "provider_error"
    message = f"edge-tts 调用失败（退出码 {returncode}）；原因未确认"
    if kind in {"WSServerHandshakeError", "ClientResponseError"}:
        status_match = re.match(r"([1-5]\d{2})(?:\s*,|\s*$)", detail)
        if status_match:
            status = status_match.group(1)
            code = "http_" + status if status in {"401", "403", "429"} else "http_error"
            message = f"语音服务返回 HTTP {status}；检查服务状态、客户端版本及宿主允许的连接方式"
    elif kind == "NoAudioReceived":
        code, message = "no_audio_received", "连接未返回音频；检查当前声线、短句基线与服务状态，原因未确认"
    elif kind in {"ClientConnectorCertificateError", "ClientConnectorSSLError", "SSLCertVerificationError", "SSLError"}:
        code, message = "tls_error", "TLS/证书检查失败；检查系统时间与证书链，保留证书校验"
    elif kind in {"ClientConnectorError", "ClientConnectorDNSError", "ClientProxyConnectionError", "ConnectionError", "gaierror"}:
        code, message = "network_error", "网络连接失败；检查 DNS、出口及宿主已允许的代理/网络设置"
    elif kind in {"TimeoutError", "ServerTimeoutError", "ConnectionTimeoutError", "SocketTimeoutError"}:
        code, message = "timeout", "语音服务连接或读取超时；未交付音频"
    elif kind in {"UnexpectedResponse", "UnknownResponse"}:
        code, message = "protocol_error", "语音服务返回非预期协议内容；核对客户端与服务兼容性"
    elif kind == "WebSocketError":
        code, message = "websocket_error", "语音 WebSocket 报错；普通网页可达不代表语音连接可用"
    return TtsFailure(code, message)


def report_failure(code, stage, message):
    print(json.dumps({"ok": False, "error": message, "error_code": code,
                      "stage": stage}, ensure_ascii=False), file=sys.stderr)


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
    parser = SafeArgumentParser(description=__doc__)
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
    temporary = None
    stage = "input"
    try:
        args = build_parser().parse_args(argv)
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
        stage = "dependency"
        executable = shutil.which("edge-tts")
        if not executable:
            raise TtsFailure("dependency_missing", "未安装 edge-tts；请先安装 requirements-tts.txt")
        command = [executable]
        stage = "output"
        directory = output_dir(args)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = directory / f"{safe_name(args.name)}-{stamp}-{uuid.uuid4().hex[:12]}.mp3"
        descriptor, filename = tempfile.mkstemp(prefix=".tts-", suffix=".part.mp3", dir=directory)
        os.close(descriptor)
        temporary = Path(filename)
        command += ["--voice", args.voice, "--rate=" + args.rate,
                    "--volume=" + args.volume, "--pitch=" + args.pitch,
                    "--write-media", str(temporary)]
        command += ["--file", str(text_file)] if text_file else ["--text=" + text]
        stage = "synthesis"
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace",
                                timeout=args.timeout, check=False)
        if result.returncode:
            # 不把服务端日志、请求 URL 或运行环境中的凭据回显到聊天/仓库。
            raise provider_failure(result.stderr, result.returncode)
        stage = "validation"
        size = validate_audio(temporary)
        stage = "output"
        os.replace(temporary, output)
        temporary = None
        payload = {"ok": True, "path": str(output), "bytes": size, "media_type": "audio/mpeg",
                   "voice": args.voice, "pitch": args.pitch, "rate": args.rate,
                   "volume": args.volume, "provider": "edge-tts-online"}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except subprocess.TimeoutExpired:
        report_failure("timeout", stage, "edge-tts 调用超时；未交付音频")
        return 2
    except TtsFailure as exc:
        report_failure(exc.code, stage, str(exc))
        return 2
    except (OSError, ValueError) as exc:
        code = {"input": "invalid_input", "validation": "invalid_audio",
                "output": "output_error"}.get(stage, "local_error")
        report_failure(code, stage, str(exc))
        return 2
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
