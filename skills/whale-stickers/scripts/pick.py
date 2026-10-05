#!/usr/bin/env python3
"""从正式索引唯一选图；仅依赖 Python 3.9+ 标准库。"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

INDEX_REL = Path("assets/stickers/common/index.json")


def resolve_root(explicit=None):
    selected = explicit or os.environ.get("WHALE_CHAN_ROOT")
    if selected:
        root = Path(selected).expanduser().resolve()
        if not (root / INDEX_REL).is_file():
            raise ValueError("指定包目录缺少 assets/stickers/common/index.json")
        return root
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / INDEX_REL).is_file():
            return ancestor.resolve()
    raise ValueError("找不到正式索引；请指定 --root 或 WHALE_CHAN_ROOT")


def load_index(root):
    common = (root / INDEX_REL.parent).resolve(strict=True)
    common.relative_to(root)
    index = (common / "index.json").resolve(strict=True)
    if index.parent != common:
        raise ValueError("索引路径越界")
    data = json.loads(index.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("index.json 必须是非空数组")
    files, ids = set(), set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("索引条目必须是对象")
        for key in ("file", "source_id", "meaning", "usage", "sha256"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError("索引缺少非空字段：" + key)
        name = item["file"]
        if name in (".", "..") or any(c in name for c in ("/", "\\", "\0", ":")):
            raise ValueError("索引文件名必须是 common 内的单一文件名")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", item["sha256"]):
            raise ValueError("索引 SHA256 格式无效")
        if not isinstance(item.get("text_note", ""), str):
            raise ValueError("text_note 必须是字符串")
        file_key, id_key = name.casefold(), item["source_id"].casefold()
        if file_key in files or id_key in ids:
            raise ValueError("索引包含重复文件名或 source_id")
        files.add(file_key)
        ids.add(id_key)
    return common, data


def load_variants(common, data):
    path = common / "variants.json"
    if not path.exists():
        return {}
    path = path.resolve(strict=True)
    if path.parent != common:
        raise ValueError("variants.json 路径越界")
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("variants.json 必须是数组")
    indexed = {x["file"]: x for x in data}
    variants = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("透明元数据条目必须是对象")
        name = entry.get("file")
        if not isinstance(name, str) or name not in indexed or name in variants:
            raise ValueError("透明元数据包含重复或未入索引的文件")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or digest.lower() != indexed[name]["sha256"].lower():
            raise ValueError("透明元数据与正式索引 SHA256 不一致")
        background, alpha = entry.get("background"), entry.get("has_alpha")
        low, high = entry.get("alpha_min"), entry.get("alpha_max")
        if (background not in ("transparent", "opaque") or not isinstance(alpha, bool)
                or not isinstance(low, int) or not isinstance(high, int)
                or not 0 <= low <= high <= 255
                or alpha != (low < 255) or alpha != (background == "transparent")):
            raise ValueError("透明元数据无效；有 alpha 通道不等于有透明像素")
        variants[name] = entry
    return variants


def select(data, query):
    q = query.strip().casefold()
    if not q:
        raise ValueError("查询不能为空")
    matches = [x for x in data if q in
               (x["file"].casefold(), Path(x["file"]).stem.casefold(), x["source_id"].casefold())]
    numeric = bool(re.fullmatch(r"[0-9]{1,2}", q))
    if not matches and numeric:
        matches = [x for x in data if x["file"].startswith(q.zfill(2) + "_")]
    if not matches and not numeric:
        matches = [x for x in data if q in x["meaning"].casefold() or q in x["file"].casefold()]
    if len(matches) != 1:
        if not matches:
            raise ValueError("没有匹配贴图；请先运行 list")
        raise ValueError("匹配不唯一；请使用完整文件名或 source_id：" +
                         ", ".join(x["file"] for x in matches))
    return matches[0]


def verified_record(common, item):
    path = (common / item["file"]).resolve(strict=True)
    if path.parent != common or not path.is_file():
        raise ValueError("贴图不是 common 内的文件，或路径越界")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    size = path.stat().st_size
    if size == 0 or digest.hexdigest() != item["sha256"].lower():
        raise ValueError("贴图为空或 SHA256 与正式索引不一致")
    if "bytes" in item and item["bytes"] != size:
        raise ValueError("贴图大小与正式索引不一致")
    return {"path": str(path), "file": item["file"], "source_id": item["source_id"],
            "meaning": item["meaning"], "usage": item["usage"],
            "text_note": item.get("text_note", ""), "sha256": digest.hexdigest(),
            "sha256_verified": True, "bytes": size}



def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    def options(target, suppress=False):
        default = argparse.SUPPRESS if suppress else None
        target.add_argument("--root", default=default, help="包数据根目录；优先于 WHALE_CHAN_ROOT")
        target.add_argument("--format", choices=("json", "path"),
                            default=argparse.SUPPRESS if suppress else "json",
                            help="默认 JSON；path 只输出已校验的本地文件路径")
        target.add_argument("--transparent-only", action="store_true",
                            default=argparse.SUPPRESS if suppress else False,
                            help="仅从已核验的真实透明图中匹配；仍需符合语义")
    options(parser)
    subs = parser.add_subparsers(dest="command", required=True)
    listing = subs.add_parser("list", help="列出语义、限制、路径并校验全部正式贴图")
    options(listing, True)
    picking = subs.add_parser("pick", help="按文件名、source_id、原图编号或唯一语义选图")
    picking.add_argument("query")
    options(picking, True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        root = resolve_root(args.root)
        common, data = load_index(root)
        variants = load_variants(common, data)
        if args.transparent_only:
            if len(variants) != len(data):
                raise ValueError("--transparent-only 需要覆盖完整索引的 variants.json")
            data = [x for x in data if variants[x["file"]]["background"] == "transparent"]
            if not data:
                raise ValueError("没有经核验的真实透明贴图")
        chosen = data if args.command == "list" else [select(data, args.query)]
        records = [verified_record(common, item) for item in chosen]
        for record in records:
            if record["file"] in variants:
                record["variant"] = variants[record["file"]]
        if args.format == "json":
            result = {"ok": True, "root": str(root)}
            result["entries" if args.command == "list" else "sticker"] = (
                records if args.command == "list" else records[0])
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n".join(x["path"] for x in records))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
