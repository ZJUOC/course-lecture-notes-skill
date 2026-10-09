"""讲义重建后一条命令生成全部 ADHD 派生版本，只打印摘要（省 token）。

python3 derive.py            同步 assets → ADHD版 → 大纲版 → 概念图版
python3 derive.py concept    只重做概念图版（改了 概念关系/*.txt 之后）
项目根目录见 common.py（LECTURE_ROOT）。
"""
import subprocess, sys
from pathlib import Path
from common import sync_assets, ROOT, COURSES

H = Path(__file__).resolve().parent
steps = ['make_adhd.py', 'make_outline.py', 'make_concept.py']
if sys.argv[1:] == ['concept']:
    steps = steps[2:]
print('ROOT', ROOT, '课程', len(COURSES))
sync_assets()
for s in steps:
    r = subprocess.run([sys.executable, str(H / s)], cwd=H, capture_output=True, text=True)
    lines = (r.stdout + r.stderr).strip().splitlines()
    print(f'== {s}', '失败' if r.returncode else 'ok')
    for ln in lines[-12:] if r.returncode else lines:
        print('  ', ln[:160])
    if r.returncode:
        sys.exit(r.returncode)
