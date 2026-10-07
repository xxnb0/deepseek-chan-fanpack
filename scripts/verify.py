#!/usr/bin/env python3
"""Verify the reference pack. Metadata-only never claims complete image verification."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MEDIA = {'.png','.jpg','.jpeg','.webp','.gif','.mp3','.wav','.ogg','.mp4'}


def verify_pet_manifest(root, known):
    """Bind shipped atlas metadata to its recorded checks, without rerunning visual QA."""
    root=Path(root).resolve()
    base=root/'assets/pets/chatgpt'
    errors=[];checked=0;warning_count=0

    def local_path(value, parent, label):
        if not isinstance(value,str) or not value or '\\' in value:
            errors.append('Invalid pet path: '+label);return None
        try:
            relative=Path(value)
            path=(parent/relative).resolve()
            if relative.is_absolute() or urlsplit(value).scheme or not path.is_relative_to(base):
                raise ValueError
        except (OSError,ValueError,RuntimeError):
            errors.append('Invalid pet path: '+label);return None
        return path

    def read_object(path, label):
        if path is None:return None
        try:
            obj=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(obj,dict):raise ValueError('Expected a JSON object')
            return obj
        except (OSError,ValueError) as exc:
            errors.append('Pet JSON: '+label+': '+str(exc));return None

    def compare(actual, expected, label):
        for key,value in expected.items():
            candidate=actual.get(key)
            if type(candidate) is not type(value) or candidate!=value:
                errors.append(label+key)

    manifest=read_object(base/'manifest.json','manifest')
    if manifest is None:return {},errors
    if type(manifest.get('schema_version')) is not int or manifest['schema_version']!=1:
        return {},errors+['Unsupported pet-manifest schema']
    formats=manifest.get('formats')
    if not isinstance(formats,dict) or set(formats)!={'v1','v2'}:
        return {},errors+['Pet manifest must contain v1 and v2 formats']
    standard_frames=[6,8,8,4,5,8,6,6,6]
    for version in (1,2):
        name='v'+str(version);item=formats[name]
        if not isinstance(item,dict):
            errors.append('Invalid pet format: '+name);continue
        checked+=1
        expected={'width':1536,'height':1872 if version==1 else 2288,
                  'columns':8,'rows':9 if version==1 else 11,
                  'cell_width':192,'cell_height':208,'mode':'RGBA','mime_type':'image/png',
                  'frames_per_row':standard_frames+([] if version==1 else [8,8])}
        compare(item,expected,'Pet format mismatch: '+name+'/')
        if type(item.get('bytes')) is not int or item['bytes']<=0:
            errors.append('Invalid pet byte count: '+name)
        if not isinstance(item.get('sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',item['sha256']):
            errors.append('Invalid pet SHA-256: '+name)
        atlas=local_path(item.get('path'),base,name+'/path')
        if atlas is not None:
            entry=known.get(atlas.relative_to(root).as_posix())
            if not isinstance(entry,dict) or entry.get('tier')!='core':
                errors.append('Pet atlas missing from core manifest: '+name)
            else:
                compare(entry,{key:item.get(key) for key in ('bytes','sha256')},
                        'Pet/core manifest mismatch: '+name+'/')
        metadata_path=local_path(item.get('metadata'),base,name+'/metadata')
        metadata=read_object(metadata_path,name+'/metadata')
        if metadata is not None:
            compare(metadata,{'spriteVersionNumber':version},'Pet metadata mismatch: '+name+'/')
            sprite=local_path(metadata.get('spritesheetPath'),metadata_path.parent,name+'/spritesheetPath')
            if sprite is not None and sprite!=atlas:
                errors.append('Pet metadata points to a different atlas: '+name)
        structural=read_object(local_path(item.get('structural_validation'),base,name+'/structural_validation'),
                               name+'/structural_validation')
        if structural is not None:
            expected_report={key:expected[key] for key in ('width','height','columns','rows','mode')}
            expected_report.update(sha256=item.get('sha256'),encoded_bytes=item.get('bytes'),
                                   sprite_version_number=version,format='PNG')
            compare(structural,expected_report,'Pet structural report mismatch: '+name+'/')
            if structural.get('ok') is not True or structural.get('errors')!=[]:
                errors.append('Pet structural validation is not successful: '+name)
        mcp_path=local_path(item.get('mcp_read_only_validation'),base,name+'/mcp_read_only_validation')
        mcp=read_object(mcp_path,name+'/mcp_read_only_validation')
        if mcp is not None:
            compare(mcp,{'sha256':item.get('sha256')},'Pet MCP report mismatch: '+name+'/')
            reported_atlas=local_path(mcp.get('file'),mcp_path.parent,name+'/mcp_file')
            if reported_atlas is not None and reported_atlas!=atlas:
                errors.append('Pet MCP report points to a different atlas: '+name)
            result=mcp.get('result')
            content=result.get('structuredContent') if isinstance(result,dict) else None
            if not isinstance(content,dict):
                errors.append('Missing pet MCP structured result: '+name)
            else:
                expected_mcp={key:expected[key] for key in (
                    'width','height','cell_width','cell_height','mime_type','frames_per_row')}
                expected_mcp.update(file_size_bytes=item.get('bytes'),sprite_version=version)
                compare(content,expected_mcp,'Pet MCP report mismatch: '+name+'/')
                if (item.get('mcp_valid') is not True or content.get('valid') is not True
                        or content.get('errors')!=[] or result.get('isError') is True):
                    errors.append('Pet MCP validation is not successful: '+name)
    quality=read_object(local_path(manifest.get('quality_report'),base,'quality_report'),'quality_report')
    if quality is not None and isinstance(formats.get('v2'),dict):
        compare(quality,{'sha256':formats['v2'].get('sha256'),
                         'encoded_bytes':formats['v2'].get('bytes')},'Pet quality report mismatch: ')
        if quality.get('ok') is not True or quality.get('errors')!=[]:
            errors.append('Pet quality report is not successful')
        warnings=quality.get('warnings')
        if not isinstance(warnings,list) or not all(isinstance(value,str) for value in warnings):
            errors.append('Invalid pet quality warnings')
        else:warning_count=len(warnings)
    return {'pet_formats_metadata_checked':checked,'pet_quality_report_warnings':warning_count},errors


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
            if path.suffix not in {'.md','.html'}:continue
            text=path.read_text(encoding='utf-8')
            targets=re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)',text)
            targets+=re.findall(r'<(?:img|audio|source)\b[^>]*?\bsrc=[\"\']([^\"\']+)[\"\']',text,re.I)
            for target in targets:
                parts=urlsplit(target)
                if parts.scheme or parts.netloc or not parts.path:continue
                destination=(path.parent/unquote(parts.path)).resolve();links+=1
                if not destination.is_relative_to(root):errors.append('Outside document link: '+str(path.relative_to(root))+' -> '+target);continue
                rel=destination.relative_to(root).as_posix()
                if not destination.exists() and not (metadata_only and rel in known and destination.suffix.lower() in MEDIA):
                    errors.append('Broken document link: '+str(path.relative_to(root))+' -> '+target)
        except (ValueError,SyntaxError,UnicodeError) as exc:errors.append('Parse: '+str(path.relative_to(root))+': '+str(exc))
    for skill in ('whale-stickers','whale-tts'):
        path=root/'skills'/skill/'SKILL.md'
        text=path.read_text(encoding='utf-8')
        if not text.startswith('---\n') or '\n---\n' not in text[4:]:errors.append('Invalid skill header: '+skill)
        else:
            front=text.split('---',2)[1]
            for key in ('name','description','version'):
                if not re.search(r'^'+key+r':\s*\S',front,re.M):errors.append('Missing skill field: '+skill+'/'+key)
    pet_stats,pet_errors=verify_pet_manifest(root,known)
    errors.extend(pet_errors)
    return {**pet_stats,'ok':not errors,'mode':'metadata-only' if metadata_only else 'full-core',
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
