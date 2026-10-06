#!/usr/bin/env python3
"""Validate a real 9-row atlas; package only on explicit caller visual attestation."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def profile() -> dict:
    value = json.loads((ROOT / "assets/pet/atlas-profile.json").read_text(encoding="utf-8"))
    if (value["id"], value["columns"], value["rows"], value["cell_width"], value["cell_height"]) != (
            "codex-public-9row", 8, 9, 192, 208):
        raise ValueError("unsupported_profile")
    return value


def image_library():
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("optional_pillow_dependency_missing") from exc
    return Image


def validate(path: Path) -> dict:
    Image = image_library()
    spec = profile()
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 50 * 1024 * 1024:
        raise ValueError("invalid_local_candidate_file")
    errors, rows = [], []
    with Image.open(path) as source:
        if source.format not in {"PNG", "WEBP"} or getattr(source, "n_frames", 1) != 1:
            raise ValueError("candidate_must_be_single_png_or_webp_atlas")
        if source.size != (spec["width"], spec["height"]):
            raise ValueError("atlas_dimensions_do_not_match_9row_contract")
        atlas = source.convert("RGBA")
    cw, ch = spec["cell_width"], spec["cell_height"]
    policy = spec["pack_quality_policy_not_upstream_protocol"]
    margin = policy["minimum_margin_px"]
    for state in spec["states"]:
        hashes, boxes = [], []
        for column in range(spec["columns"]):
            x, y = column * cw, state["row"] * ch
            cell = atlas.crop((x, y, x + cw, y + ch))
            alpha = cell.getchannel("A")
            box = alpha.getbbox()
            key = state["name"] + ":" + str(column)
            if column >= state["frames"]:
                if box is not None:
                    errors.append("unused_cell_not_transparent:" + key)
                continue
            if box is None:
                errors.append("used_cell_empty:" + key)
                continue
            boxes.append(list(box))
            if box[0] < margin or box[1] < margin or box[2] > cw - margin or box[3] > ch - margin:
                errors.append("subject_touches_cell_margin:" + key)
            visible = sum(alpha.histogram()[1:]) / (cw * ch)
            if visible < policy["minimum_visible_fraction"]:
                errors.append("subject_too_small_for_pack_policy:" + key)
            # Ignore hidden RGB under zero alpha when detecting identical frames.
            normalized = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            normalized.alpha_composite(cell)
            hashes.append(hashlib.sha256(normalized.tobytes()).hexdigest())
        distinct = len(set(hashes))
        if len(hashes) == state["frames"] and distinct <= 1:
            errors.append("state_has_no_frame_variation:" + state["name"])
        rows.append({"name": state["name"], "frames_found": len(hashes),
                     "distinct_frames": distinct, "bounds": boxes})
    return {"ok": not errors, "profile": spec["id"], "width": atlas.width,
            "height": atlas.height, "used_cells_expected": sum(x["frames"] for x in spec["states"]),
            "rows": rows, "errors": errors, "visual_semantics_verified": False,
            "host_import_verified": False}


def preview(title: str, spec: dict) -> str:
    # Local image and inline code only. Rendering an existing candidate is not art generation.
    states = json.dumps(spec["states"], ensure_ascii=False)
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>""" + html.escape(title) + """ · 候选预览</title>
<style>body{font:16px system-ui;margin:2rem}main{display:flex;flex-wrap:wrap;gap:1rem}
figure{margin:0}canvas{border:1px solid #888;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 0/20px 20px}
button{font:inherit;padding:.4rem .8rem}img{max-width:100%;height:auto}</style>
<h1>""" + html.escape(title) + """ · 候选预览</h1>
<p>只读本地播放；请检查角色、动作、尾巴、循环与裁切。预览不是宿主导入成功。</p>
<button id="toggle" type="button">暂停 / 继续</button><main id="states"></main>
<h2>完整接触表</h2><img src="spritesheet.webp" alt="候选完整网格">
<script>
const states=""" + states + """;
const image=new Image(); let paused=matchMedia('(prefers-reduced-motion: reduce)').matches;
document.getElementById('toggle').onclick=()=>{paused=!paused};
image.onload=()=>states.forEach(state=>{
 const figure=document.createElement('figure'), canvas=document.createElement('canvas');
 canvas.width=192;canvas.height=208; const label=document.createElement('figcaption');
 label.textContent=state.name;figure.append(canvas,label);document.getElementById('states').append(figure);
 const ctx=canvas.getContext('2d');let frame=0;
 function tick(){ctx.clearRect(0,0,192,208);ctx.drawImage(image,frame*192,state.row*208,192,208,0,0,192,208);
 const delay=state.durations_ms[frame];if(!paused)frame=(frame+1)%state.frames;setTimeout(tick,delay)}tick();
}); image.src='spritesheet.webp';
</script></html>"""


def package(path: Path, output: Path, pet_id: str, name: str, visual_confirmed: bool) -> dict:
    if not visual_confirmed:
        raise ValueError("visual_review_confirmation_required")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", pet_id) or len(pet_id) > 64:
        raise ValueError("invalid_pet_id")
    if not name.strip() or len(name) > 100:
        raise ValueError("invalid_display_name")
    result = validate(path)
    if not result["ok"]:
        raise ValueError("candidate_failed_structural_validation")
    if output.is_symlink() or output.exists():
        raise ValueError("output_directory_already_exists")
    Image = image_library()
    output.mkdir(parents=True, exist_ok=False)
    with Image.open(path) as source:
        rgba = source.convert("RGBA")
        rgba.save(output / "spritesheet.webp", "WEBP", lossless=True, quality=100, exact=True)
    with Image.open(output / "spritesheet.webp") as exported:
        if exported.convert("RGBA").tobytes() != rgba.tobytes():
            raise ValueError("lossless_export_roundtrip_mismatch")
    if not validate(output / "spritesheet.webp")["ok"]:
        raise ValueError("candidate_failed_structural_validation")
    pet = {"id": pet_id, "displayName": name,
           "description": "鲸鱼娘社区二创桌宠；非官方角色。",
           "spritesheetPath": "spritesheet.webp"}
    (output / "pet.json").write_text(json.dumps(pet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "preview.html").write_text(preview(name, profile()), encoding="utf-8")
    receipt = {"ok": True, "profile": profile()["id"],
               "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "spritesheet_sha256": hashlib.sha256((output / "spritesheet.webp").read_bytes()).hexdigest(),
               "structural_validation_passed": True,
               "visual_review": "caller_attested_not_automatically_verified",
               "host_import_verified": False, "host_settings_modified": False}
    (output / "validation-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--id", default="deepseek-whale-chan")
    parser.add_argument("--name", default="鲸鱼娘")
    parser.add_argument("--visual-review-confirmed", action="store_true")
    args = parser.parse_args(argv)
    try:
        candidate = args.input.expanduser()
        result = package(candidate, args.output_dir.expanduser(), args.id, args.name, args.visual_review_confirmed) if args.output_dir else validate(candidate)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2
    except (OSError, ValueError) as exc:
        known = {"optional_pillow_dependency_missing", "unsupported_profile", "invalid_local_candidate_file",
                 "candidate_must_be_single_png_or_webp_atlas", "atlas_dimensions_do_not_match_9row_contract",
                 "visual_review_confirmation_required", "invalid_pet_id", "invalid_display_name",
                 "candidate_failed_structural_validation", "output_directory_already_exists",
                 "lossless_export_roundtrip_mismatch"}
        code = str(exc) if type(exc) is ValueError and str(exc) in known else "candidate_read_or_write_failed"
        print(json.dumps({"ok": False, "error_code": code, "host_import_verified": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
