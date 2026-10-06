#!/usr/bin/env python3
"""Check/sync persona mirrors, or export reviewed materials without installing them."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/xxnb0/deepseek-chan-fanpack"
PREAMBLE = "# 独立角色提示\n\n与 SOUL.md 是等价入口，选一份即可。\n\n"
TARGETS = ("all", "prompt", "hermes", "openclaw", "card-v2")


def read_lf(path: Path) -> str:
    if path.is_symlink():
        raise ValueError("source_symlink_not_allowed")
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(root: Path) -> tuple[str, dict]:
    soul = read_lf(root / "SOUL.md")
    sections = soul.split("---", 2)
    if not soul.startswith("---\n") or len(sections) != 3 or not sections[2].strip():
        raise ValueError("invalid_soul_frontmatter_or_body")
    persona = json.loads(read_lf(root / "personality.json"))
    if not isinstance(persona, dict):
        raise ValueError("invalid_personality_object")
    for field in ("name", "style", "lang"):
        if not isinstance(persona.get(field), str) or not persona[field].strip():
            raise ValueError("missing_personality_metadata_" + field)
    return sections[2].strip(), persona


def check(root: Path) -> dict:
    body, persona = load(root)
    errors = []
    if not isinstance(persona.get("body"), str) or persona["body"].strip() != body:
        errors.append("personality_body_drift")
    if read_lf(root / "prompts/system.md").strip() != (PREAMBLE + body).strip():
        errors.append("system_prompt_drift")
    return {"ok": not errors, "source_body_sha256": digest(body), "errors": errors}


def atomic_text(path: Path, text: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError("derived_source_must_be_existing_regular_file")
    descriptor, name = tempfile.mkstemp(prefix=".persona-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.chmod(name, path.stat().st_mode & 0o777)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def sync(root: Path) -> dict:
    body, persona = load(root)
    # Both destinations are checked before either known derived file is changed.
    destinations = (root / "personality.json", root / "prompts/system.md")
    if any(p.is_symlink() or not p.is_file() for p in destinations):
        raise ValueError("derived_source_must_be_existing_regular_file")
    persona["body"] = body
    atomic_text(destinations[0], json_text(persona))
    atomic_text(destinations[1], PREAMBLE + body + "\n")
    return check(root)


def portable_links(text: str, source_path: str) -> str:
    base = REPOSITORY + "/blob/main/" + source_path

    def replace(match: re.Match) -> str:
        target = match.group(1)
        parts = urlsplit(target)
        if parts.scheme or parts.netloc or not parts.path:
            return match.group(0)
        return "](" + urljoin(base, target) + ")"

    return re.sub(r"\]\(([^\s)]+)\)", replace, text)


def build_exports(root: Path, target: str = "all") -> tuple[dict[str, str], dict]:
    if target not in TARGETS:
        raise ValueError("unknown_export_target")
    report = check(root)
    if not report["ok"]:
        raise ValueError("persona_mirrors_drifted_run_check")
    body, persona = load(root)
    body = portable_links(body, "SOUL.md")
    identity = portable_links(read_lf(root / "IDENTITY.md"), "IDENTITY.md").strip()
    fragment = read_lf(root / "adapters/AGENTS.fragment.md")
    source_hashes = {name: digest(read_lf(root / name)) for name in (
        "SOUL.md", "IDENTITY.md", "adapters/AGENTS.fragment.md")}
    source_hashes["personality_metadata"] = digest(json.dumps(
        {key: persona[key] for key in ("name", "style", "lang")},
        ensure_ascii=False, sort_keys=True))
    source_id = digest(json.dumps(source_hashes, sort_keys=True))
    files = {}
    if target in ("all", "prompt"):
        files["prompt.txt"] = body + "\n\n" + identity + "\n"
    if target in ("all", "hermes", "openclaw"):
        files["SOUL.md"] = body + "\n"
    if target in ("all", "openclaw"):
        files["IDENTITY.md"] = identity + "\n"
        files["AGENTS.fragment.md"] = fragment
    if target in ("all", "card-v2"):
        card = {
            "spec": "chara_card_v2", "spec_version": "2.0",
            "data": {
                "name": persona["name"], "description": body + "\n\n" + identity,
                "personality": persona["style"],
                "scenario": "社区二创鲸鱼娘的日常助手演绎；不冒充官方模型身份。",
                "first_mes": "在呢。今天有什么想一起琢磨的？",
                "mes_example": "<START>\n{{user}}: 做得不错。\n{{char}}: 这次我也挺满意的。那个边角终于也顾到了。",
                "creator_notes": "Fan adaptation, not official canon. Sources and material rights: " + REPOSITORY,
                "system_prompt": "", "post_history_instructions": "",
                "alternate_greetings": ["鱼已经靠岸了，说吧。"],
                "tags": ["鲸鱼娘", "DeepSeek-chan", "fan-adaptation"],
                "creator": "xxnb0/deepseek-chan-fanpack",
                "character_version": source_id[:12],
                "extensions": {"deepseek_chan": {
                    "source_sha256": source_id, "host_runtime_verified": False,
                    "voice_and_avatar_configured": False}}
            }
        }
        files["character-card-v2.json"] = json_text(card)
    files["README.md"] = (
        "# 待导入角色材料\n\n来源：" + REPOSITORY + "\n\n"
        "这里的文件只是导出候选，没有修改宿主设置，也没有安装头像、宠物或声音。"
        "请先读取来源仓库 docs/platform-adapters.md；确认真实角色载体、保存原值后再合并。"
        "AGENTS.fragment.md 不是整个全局 AGENTS 的替代品。"
        "正文中 docs 路径属于来源仓库；未随文字复制图片附件。\n"
    )
    receipt = {
        "schema_version": 1, "target": target, "source_repository": REPOSITORY,
        "source_sha256": source_id, "source_hashes_lf_normalized": source_hashes,
        "host_settings_modified": False, "host_runtime_verified": False,
        "files": [{"path": name, "bytes": len(text.encode("utf-8")), "sha256": digest(text)}
                  for name, text in sorted(files.items())]
    }
    return files, receipt


def export(root: Path, destination: Path, target: str = "all") -> dict:
    files, receipt = build_exports(root, target)
    if destination.is_symlink() or destination.exists():
        raise ValueError("output_directory_already_exists")
    destination.mkdir(parents=True, exist_ok=False)
    for name, text in files.items():
        with (destination / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    with (destination / "export-manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json_text(receipt))
    return {"ok": True, "output_dir": str(destination), "target": target,
            "file_count": len(files) + 1, "host_settings_modified": False,
            "host_runtime_verified": False, "source_sha256": receipt["source_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--sync", action="store_true")
    group.add_argument("--output-dir", type=Path)
    parser.add_argument("--target", choices=TARGETS, default="all")
    args = parser.parse_args(argv)
    try:
        root = args.root.expanduser().resolve(strict=True)
        result = check(root) if args.check else sync(root) if args.sync else export(
            root, args.output_dir.expanduser().absolute(), args.target)
        print(json_text(result), end="")
        return 0 if result["ok"] else 2
    except (OSError, ValueError, TypeError, KeyError) as exc:
        # No raw filesystem/provider messages, environment or private paths.
        print(json_text({"ok": False, "error_type": type(exc).__name__,
                         "error": "export_failed_check_sources_and_new_destination"}), file=sys.stderr, end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
