#!/usr/bin/env python3
"""只列出课程目录里“还没处理过”的材料，代替 ls + shasum + 翻记录（省 token）。

用法：new_materials.py <材料目录或文件...>          打印新文件（SHA-256 前 12 位不在记录里）
      new_materials.py --mark <材料目录...>   处理完后登记，下次不再列出
已知指纹 = ROOT/制作记录/*.md 与 制作记录/归档/*.md 里出现的 12 位以上十六进制串 ∪ ROOT/制作记录/材料指纹.json。
ROOT 同 reader/common.py（环境变量 LECTURE_ROOT）。
"""
import hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'reader'))
from common import REC

SKIP = {'.DS_Store'}
args = sys.argv[1:]
mark = '--mark' in args
dirs = [Path(a).expanduser() for a in args if a != '--mark']
db_path = REC / '材料指纹.json'
db = json.loads(db_path.read_text()) if db_path.exists() else {}
known = set(db.values())
for md in [*REC.glob('*.md'), *REC.glob('归档/*.md')]:
    known |= {h[:12] for h in re.findall(r'\b[0-9a-f]{12,64}\b', md.read_text())}

new = []
for d in dirs:
    for f in sorted(p for p in ([d] if d.is_file() else d.rglob('*')) if p.is_file() and p.name not in SKIP and not p.name.startswith('~$')):
        h = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
        if h not in known:
            new.append((f, h))
for f, h in new:
    print(h, f'{f.stat().st_size/1e6:6.1f}MB', f)
print(f'共 {len(new)} 个新文件' + ('，已登记' if mark and new else ''))
if mark and new:
    db.update({str(f): h for f, h in new})
    db_path.write_text(json.dumps(db, ensure_ascii=False, indent=1))
