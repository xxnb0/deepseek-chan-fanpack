#!/usr/bin/env python3
"""Verify checksums, picture tiers, skill entry points and Python syntax."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    with p.open('rb') as f:
        h = hashlib.sha256()
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',action='store_true',help='Also require and verify extracted attic images')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'manifest.json').read_text())
    errors=[]
    checked=0
    for item in manifest['files']:
        rel=Path(item['path'])
        p=(ROOT/rel).resolve()
        if not p.is_relative_to(ROOT):
            errors.append('Outside path: '+str(rel));continue
        if item.get('tier')=='archive' and not args.archive:
            continue
        if not p.is_file():
            errors.append('Missing: '+str(rel));continue
        if p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:
            errors.append('Checksum mismatch: '+str(rel))
        checked+=1
    index=json.loads((ROOT/'assets/stickers/common/index.json').read_text())
    if len(index)!=33: errors.append('Expected 33 common stickers')
    for x in index:
        p=ROOT/'assets/stickers/common'/x['file']
        if not p.is_file() or sha(p)!=x['sha256']:
            errors.append('Common index mismatch: '+x['file'])
    variants=json.loads((ROOT/'assets/stickers/common/variants.json').read_text())
    if {x['file'] for x in variants}!={x['file'] for x in index}:
        errors.append('Variants/index file set mismatch')
    for skill in ('whale-stickers','minis-tts'):
        s=ROOT/'skills'/skill/'SKILL.md'
        if not s.is_file() or not s.read_text().startswith('---\n'):
            errors.append('Invalid skill entry: '+skill)
    for p in ROOT.rglob('*.py'):
        if '.git' not in p.parts:
            try: compile(p.read_text(),str(p),'exec')
            except SyntaxError as e: errors.append('Syntax: '+str(e))
    print(json.dumps({'ok':not errors,'checked_files':checked,'common_stickers':len(index),'transparent_stickers':sum(x['background']=='transparent' for x in variants),'archive_required':args.archive,'errors':errors},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':
    raise SystemExit(main())
