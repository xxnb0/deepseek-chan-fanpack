#!/usr/bin/env python3
"""Verify the reference pack. Metadata-only never claims complete image verification."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MEDIA = {'.png','.jpg','.jpeg','.webp','.gif','.mp3','.wav','.ogg'}


def sha(path):
    with path.open('rb') as handle:
        digest=hashlib.sha256()
        for chunk in iter(lambda:handle.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify(root, metadata_only=False, archive=False):
    root=root.resolve()
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    errors=[];checked=0;media_checked=0;skipped=[];seen=set()
    for item in manifest['files']:
        rel=Path(item['path']);path=(root/rel).resolve()
        if rel.is_absolute() or not path.is_relative_to(root):
            errors.append('Outside path: '+str(rel));continue
        if str(rel) in seen:errors.append('Duplicate manifest path: '+str(rel))
        seen.add(str(rel))
        if item.get('tier')=='archive' and not archive:continue
        if metadata_only and path.suffix.lower() in MEDIA and not path.is_file():
            skipped.append(str(rel));continue
        if not path.is_file():errors.append('Missing: '+str(rel));continue
        if path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:
            errors.append('Checksum mismatch: '+str(rel))
        checked+=1
        if path.suffix.lower() in MEDIA:media_checked+=1
    known={x['path']:x for x in manifest['files']}
    index=json.loads((root/'assets/stickers/common/index.json').read_text(encoding='utf-8'))
    variants=json.loads((root/'assets/stickers/common/variants.json').read_text(encoding='utf-8'))
    if len(index)!=manifest['common']['count']:errors.append('Common count mismatch')
    if {x['file'] for x in variants}!={x['file'] for x in index}:errors.append('Variants/index file set mismatch')
    for item in index:
        rel='assets/stickers/common/'+item['file']
        if '/' in item['file'] or '\\' in item['file'] or item['file'] in {'.','..'}:
            errors.append('Invalid common filename: '+item['file']);continue
        entry=known.get(rel,{})
        if item['sha256']!=entry.get('sha256'):errors.append('Index/manifest mismatch: '+rel)
        if 'bytes' in item and item['bytes']!=entry.get('bytes'):errors.append('Index size mismatch: '+rel)
    by_file={x['file']:x for x in index}
    for v in variants:
        if v['sha256']!=by_file.get(v['file'],{}).get('sha256'):errors.append('Variant hash mismatch: '+v['file'])
        if v['background'] not in {'transparent','opaque'} or v['has_alpha']!=(v['alpha_min']<255) or v['has_alpha']!=(v['background']=='transparent'):
            errors.append('Invalid alpha metadata: '+v['file'])
    # Markdown file links are checked even in metadata mode. Only known, unchanged
    # media may be absent locally in that mode; arbitrary missing files still fail.
    links=0
    for path in root.rglob('*'):
        if not path.is_file() or any(p in {'.git','.venv','__pycache__','output'} for p in path.relative_to(root).parts):continue
        try:
            if path.suffix=='.json':json.loads(path.read_text(encoding='utf-8'))
            if path.suffix=='.py':compile(path.read_text(encoding='utf-8'),str(path),'exec')
            if path.suffix!='.md':continue
            text=path.read_text(encoding='utf-8')
            for target in re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)',text):
                parts=urlsplit(target)
                if parts.scheme or parts.netloc or not parts.path:continue
                destination=(path.parent/unquote(parts.path)).resolve();links+=1
                if not destination.is_relative_to(root):errors.append('Outside document link: '+str(path.relative_to(root))+' -> '+target);continue
                rel=destination.relative_to(root).as_posix()
                if not destination.exists() and not (metadata_only and rel in known and destination.suffix.lower() in MEDIA):
                    errors.append('Broken document link: '+str(path.relative_to(root))+' -> '+target)
        except (ValueError,SyntaxError,UnicodeError) as exc:errors.append('Parse: '+str(path.relative_to(root))+': '+str(exc))
    for skill in ('whale-stickers','minis-tts'):
        path=root/'skills'/skill/'SKILL.md'
        text=path.read_text(encoding='utf-8')
        if not text.startswith('---\n') or '\n---\n' not in text[4:]:errors.append('Invalid skill header: '+skill)
        else:
            front=text.split('---',2)[1]
            for key in ('name','description','version'):
                if not re.search(r'^'+key+r':\s*\S',front,re.M):errors.append('Missing skill field: '+skill+'/'+key)
    return {'ok':not errors,'mode':'metadata-only' if metadata_only else 'full-core',
            'checked_files':checked,'media_files_byte_verified':media_checked,
            'media_files_not_byte_verified':skipped,'full_media_verification':not skipped and not errors,
            'common_stickers':len(index),'transparent_stickers':sum(x['background']=='transparent' for x in variants),
            'archive_required':archive,'local_links_checked':links,'errors':errors}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',action='store_true',help='Require the separately obtained archive images too')
    parser.add_argument('--metadata-only',action='store_true',help='Allow missing image bytes; verify existing bytes and metadata, explicitly report skips')
    args=parser.parse_args()
    if args.archive and args.metadata_only:parser.error('--archive cannot be combined with --metadata-only')
    result=verify(ROOT,args.metadata_only,args.archive)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
