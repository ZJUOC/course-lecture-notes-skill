#!/usr/bin/env python3
"""从源文件重建全部讲义：ROOT/制作记录/构建/*构建配置.json 逐个 build_lecture.py，再 reader/derive.py 生成读者打开的页面。

python3 build_all.py          只打印每门课一行摘要
复现检查：在副本里跑完后与原成品逐字节比较（cmp），见 references/standards.md“复现”。
"""
import json, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H / 'reader'))
from common import REC

cfgs = sorted((REC / '构建').glob('*构建配置.json'))
for cfg in cfgs:
    r = subprocess.run([sys.executable, str(H / 'build_lecture.py'), str(cfg)], capture_output=True, text=True)
    if r.returncode:
        print(cfg.name, '失败\n', r.stderr[-1500:]); sys.exit(1)
    j = json.loads(r.stdout.strip().splitlines()[-1])
    print(f'{cfg.stem}: {Path(j["output"]).name}  公式 {j["math"]}  图 {j["figures"]}  块 {sum(j["blocks"].values())}',
          f'pandoc 警告：{j["pandoc_warnings"][:200]}' if j['pandoc_warnings'] else '')
r = subprocess.run([sys.executable, str(H / 'reader' / 'derive.py')], cwd=H / 'reader', capture_output=True, text=True)
print((r.stdout + r.stderr[-1500:] if r.returncode else r.stdout).strip())
sys.exit(r.returncode)
