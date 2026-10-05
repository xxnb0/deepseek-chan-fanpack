#!/usr/bin/env python3
"""Pick a vetted whale-maid sticker and print a valid Minis inline image."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path('/var/minis/shared/鲸鱼娘女仆表情包/鲸鱼娘_常用表情精选')
INDEX = ROOT / '使用索引.json'

def entries():
    data = json.loads(INDEX.read_text(encoding='utf-8'))
    if not isinstance(data,list): raise ValueError('使用索引.json不是数组')
    return data

def main():
    parser=argparse.ArgumentParser(description='选择已核验的鲸鱼娘常用表情')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('list',help='列出可用贴图与使用语境')
    pick=sub.add_parser('pick',help='按编号、文件名或含义选择贴图')
    pick.add_argument('query');pick.add_argument('--json',action='store_true',help='返回路径、语义、限制和内嵌语法')
    pick.add_argument('--verify-sha256',action='store_true',help='额外校验文件内容哈希')
    args=parser.parse_args();data=entries()
    if args.command=='list':
        for x in data: print(f"{x['file']}\t{x['meaning']}\t{x['usage']}")
        return 0
    q=args.query.strip().lower()
    exact=[x for x in data if q in (x['file'].lower(), Path(x['file']).stem.lower(), x['source_id'].lower())]
    if not exact and q.isdigit():
        # Legacy 01-17 remain stable. New stickers use 新Q_01..16 or SUNBURST-01..16.
        exact=[x for x in data if not x['file'].startswith('新Q_') and x['file'].startswith(q.zfill(2)+'_')]
    if exact: matches=exact
    else:
        matches=[x for x in data if q in x['meaning'].lower() or q in x['file'].lower()]
    if not matches:
        print('无对应贴图；不要猜测文件名。请先运行 list。',file=sys.stderr);return 2
    if len(matches)>1:
        print('名称含糊，请用完整文件名或序号：'+', '.join(x['file'] for x in matches),file=sys.stderr);return 2
    x=matches[0];p=ROOT/x['file']
    if not p.is_file() or p.parent!=ROOT:
        print('贴图文件不存在，取消发送。',file=sys.stderr);return 3
    if args.verify_sha256:
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        if h!=x['sha256']:
            print('贴图内容与索引哈希不一致，取消发送。',file=sys.stderr);return 4
    url='minis://shared/'+quote('鲸鱼娘女仆表情包/鲸鱼娘_常用表情精选/'+x['file'],safe='/')
    embed=f"![鲸鱼娘·{x['meaning']}]({url})"
    if args.json: print(json.dumps({'file':str(p),'source_id':x['source_id'],'meaning':x['meaning'],'usage':x['usage'],'text_note':x.get('text_note',''),'embed':embed},ensure_ascii=False,indent=2))
    else:print(embed)
    return 0

if __name__=='__main__':sys.exit(main())
