"""由 ADHD 版生成 ADHD 大纲版：荧光标注不变，右侧阅读地图换成跟随阅读位置的概念大纲，并给右下角手写小窗留位置。

用法：先跑 make_adhd.py，再 python3 make_outline.py（通常由 derive.py 调用）
输入：ROOT/NN *（ADHD版）.html；输出：ROOT/NN *（ADHD大纲版）.html。ADHD 版本身不改动。
"""
import hashlib, re
from pathlib import Path
from common import ROOT, COURSES

T = ROOT / 'ADHD工具'
ver = hashlib.sha1(b''.join((T / f).read_bytes() for f in ('adhd.css', 'outline.css', 'outline.js'))).hexdigest()[:8]

for c in COURSES:
    h = (ROOT / f'{c}（ADHD版）.html').read_text()
    h, n1 = re.subn(r'<script src="ADHD工具/adhd\.js\?v=\w+"></script>', f'<script src="ADHD工具/outline.js?v={ver}"></script>', h)
    h, n2 = re.subn(r'(<link href="ADHD工具/adhd\.css\?v=)\w+(" rel="stylesheet"/>)',
                    rf'\g<1>{ver}\2<link href="ADHD工具/outline.css?v={ver}" rel="stylesheet"/>', h)
    h, n3 = re.subn(r'（ADHD版）</title>', '（ADHD大纲版）</title>', h)
    assert n1 == n2 == n3 == 1, (c, n1, n2, n3)
    (ROOT / f'{c}（ADHD大纲版）.html').write_text(h)
    print(c, 'ok')
