#!/usr/bin/env python3
"""Install the character kit without exporting credentials or replacing host config."""
import argparse
import datetime
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '<!-- deepseek-chan:begin -->'
END = '<!-- deepseek-chan:end -->'


def merge(original, addition):
    section = BEGIN + '\n' + addition.rstrip() + '\n' + END
    if BEGIN in original:
        if original.count(BEGIN) != 1 or original.count(END) != 1:
            raise ValueError('Invalid existing deepseek-chan markers; merge manually.')
        left, tail = original.split(BEGIN, 1)
        _, right = tail.split(END, 1)
        return left + section + right
    return original.rstrip() + ('\n\n' if original.strip() else '') + section + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', choices=['generic', 'openclaw', 'hermes', 'cursor'], default='generic')
    p.add_argument('--workspace', required=True, help='Explicit host workspace; for Hermes use HERMES_HOME')
    p.add_argument('--dry-run', action='store_true', help='Print plan only; no changes')
    p.add_argument('--include-archive', action='store_true', help='Copy optional reference attic if extracted locally')
    p.add_argument('--replace-persona', action='store_true', help='Explicitly replace existing SOUL/IDENTITY (backed up)')
    args = p.parse_args()
    dest = Path(args.workspace).expanduser().resolve()
    if dest == ROOT or dest.is_relative_to(ROOT):
        p.error('The target cannot be inside this source repository.')
    if ROOT.is_relative_to(dest):
        p.error('Move/clone the source repository outside the target to avoid copying itself.')
    required = ['SOUL.md','GLOBAL.md','IDENTITY.md','AGENTS.md','TOOLS.md','personality.json','prompts','assets','skills','requirements-tts.txt']
    for name in required:
        if not (ROOT/name).exists():
            p.error('Source kit is incomplete: ' + name)
    attic = ROOT/'archive/reference-library'
    attic_images = [f for f in attic.glob('*') if f.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif'}]
    if args.include_archive and not attic_images:
        p.error('Optional archive images are not extracted. Use the full release bundle first.')
    skill_prefix = '.cursor/skills' if args.target == 'cursor' else 'skills'
    replace = ['SOUL.md'] + (['IDENTITY.md'] if args.target != 'hermes' else [])
    if args.target == 'cursor':
        replace = ['.cursor/rules/deepseek-chan.mdc']
        merges = {replace[0]: '---\ndescription: 鲸鱼娘（大肥鱼）人物声线与媒体技能\nalwaysApply: true\n---\n\n' + (ROOT/'prompts/system.md').read_text() + '\n\n技能路径为 .cursor/skills/whale-stickers/ 与 .cursor/skills/minis-tts/；实际资源在项目 deepseek-chan/assets/。'}
    elif args.target == 'hermes':
        merges = {'SOUL.md': (ROOT/'SOUL.md').read_text() + '\n' + (ROOT/'GLOBAL.md').read_text() + '\n\n## 媒体技能\n使用本地 skills/whale-stickers/ 与 skills/minis-tts/；资源在 deepseek-chan/assets/。只使用实际支持的消息附件工具发送。'}
    else:
        merges = {'AGENTS.md':(ROOT/'AGENTS.md').read_text(),'TOOLS.md':(ROOT/'TOOLS.md').read_text()}
        if args.target == 'openclaw':
            merges['MEMORY.md'] = (ROOT/'GLOBAL.md').read_text()
        else:
            merges['GLOBAL.md'] = (ROOT/'GLOBAL.md').read_text()
    # Preflight every text merge before touching host files.
    planned = {}
    for name, text in merges.items():
        if args.target in ('hermes', 'cursor'):
            planned[name] = text
        else:
            original = (dest/name).read_text() if (dest/name).is_file() else ''
            planned[name] = merge(original,text)
    conflicts = []
    for name in replace:
        expected = planned[name].encode('utf-8') if name in planned else (ROOT/name).read_bytes()
        if (dest/name).is_file() and (dest/name).read_bytes() != expected:
            conflicts.append(name)
    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = dest/'.deepseek-chan-backups'/timestamp
    touched = set(replace) | set(merges) | {'deepseek-chan',skill_prefix+'/whale-stickers',skill_prefix+'/minis-tts'}
    for name in touched | {'.deepseek-chan-backups'}:
        path = dest/name
        if path.is_symlink() or not path.resolve().is_relative_to(dest):
            p.error('Refusing a symlinked/outside target: ' + str(path))
    if conflicts and not args.replace_persona and not args.dry_run:
        p.error('Existing persona files: ' + ', '.join(conflicts) + '. Review --dry-run; opt in with --replace-persona.')
    plan = {'target':args.target,'workspace':str(dest),'package_root':str(dest/'deepseek-chan'),'copy_skills':['whale-stickers','minis-tts'],'replace_persona':replace,'persona_conflicts':conflicts,'merge_files':list(merges),'include_archive':args.include_archive,'backup':str(backup),'dry_run':args.dry_run}
    print(json.dumps(plan,ensure_ascii=False,indent=2))
    if args.dry_run:
        return 0
    dest.mkdir(parents=True,exist_ok=True)
    for name in sorted(touched):
        existing = dest/name
        if existing.exists():
            b = backup/name
            b.parent.mkdir(parents=True,exist_ok=True)
            if existing.is_dir(): shutil.copytree(existing,b)
            else: shutil.copy2(existing,b)
    package = dest/'deepseek-chan'
    if package.exists(): shutil.rmtree(package)
    package.mkdir()
    for name in required:
        src = ROOT/name
        out = package/name
        if src.is_dir():
            shutil.copytree(src,out,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        else: shutil.copy2(src,out)
    if args.include_archive:
        shutil.copytree(attic,package/'archive/reference-library')
    for name in replace:
        if name not in planned:
            (dest/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,dest/name)
    for name,text in planned.items():
        (dest/name).parent.mkdir(parents=True,exist_ok=True)
        (dest/name).write_text(text,encoding='utf-8')
    for skill in ('whale-stickers','minis-tts'):
        out = dest/skill_prefix/skill
        if out.exists(): shutil.rmtree(out)
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(ROOT/'skills'/skill,out,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    print('Installed. Review host persona + merged files. Install TTS dependencies separately; start a new host session.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
