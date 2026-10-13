"""由 ADHD 版生成 ADHD 概念图版：荧光标注不变，右上换成 目录 + 概念关系图，右下留给手写笔记窗口。

用法：先跑 make_adhd.py，再 python3 make_concept.py（通常由 derive.py 调用）
概念与关系是手工整理的，在 ROOT/制作记录/概念关系/<课程>.txt；本脚本先校验，再把数据嵌进页面。
词语荧光（可选）：ROOT/制作记录/词语荧光/<课程>.txt，见 keywords.py；之后按分句自动补密集荧光（dense.py，LECTURE_DENSE=0 关闭）。
概念小标题与智慧区（可选，手工）：概念关系第 4 栏注解、ROOT/制作记录/智慧/<课程>.txt，见 wisdom.py。
手写区默认尺寸取自 Trackpad Studio 手写小窗（trackpad_ink.py），读不到时用 750×470。
输入：ROOT/NN *（ADHD版）.html；输出：ROOT/NN *（ADHD概念图版）.html。ADHD 版本身不改动。
"""
import hashlib, json, os, re, sys
from common import ROOT, COURSES
from concept_map import build
from trackpad_ink import ink_size
from keywords import apply as kw_apply
from dense import apply as dense_apply
from wisdom import apply as wisdom_apply
from bs4 import BeautifulSoup

T = ROOT / 'ADHD工具'
DENSE = os.environ.get('LECTURE_DENSE', '1') != '0'  # 密集词语荧光，见 dense.py
ver = hashlib.sha1(b''.join((T / f).read_bytes() for f in ('adhd.css', 'concept.css', 'concept.js'))).hexdigest()[:8]

iw, ih, src = ink_size()
print(f'手写区默认 {iw}×{ih}（{src}）')
missing = []
for c in COURSES:
    if not (ROOT / '制作记录' / '概念关系' / f'{c}.txt').exists():
        missing.append(c)
        continue
    data, probs = build(c)
    hard = [p for p in probs if '定位词' not in p]
    if hard:
        print(c, '概念关系有错：', *hard, sep='\n  ')
        sys.exit(1)
    h = (ROOT / f'{c}（ADHD版）.html').read_text()
    blob = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    h, n1 = re.subn(r'<script src="ADHD工具/adhd\.js\?v=\w+"></script>',
                    f'<script id="concept-data" type="application/json" data-ink="{iw}x{ih}">{blob}</script>'
                    f'<script src="ADHD工具/concept.js?v={ver}"></script>', h)
    h, n2 = re.subn(r'(<link href="ADHD工具/adhd\.css\?v=)\w+(" rel="stylesheet"/>)',
                    rf'\g<1>{ver}\2<link href="ADHD工具/concept.css?v={ver}" rel="stylesheet"/>', h)
    h, n3 = re.subn(r'（ADHD版）</title>', '（ADHD概念图版）</title>', h)
    assert n1 == n2 == n3 == 1, (c, n1, n2, n3)
    kw = ''
    soup = BeautifulSoup(h, 'html.parser')
    if (ROOT / '制作记录' / '词语荧光' / f'{c}.txt').exists():
        done, bold, miss = kw_apply(soup, c)
        kw = f'词语荧光 {done} 处' + (f'，{len(miss)} 个问题：' + '；'.join(miss) if miss else '')
    if DENSE:
        kw += f'  密集荧光 {dense_apply(soup, c)} 处'
    nh, nw, wp = wisdom_apply(soup, c)
    if nh or nw or wp:
        kw += f'  概念小标题 {nh} 个  智慧 {nw} 个单元' + (f'，{len(wp)} 个问题：' + '；'.join(wp) if wp else '')
    h = str(soup)
    (ROOT / f'{c}（ADHD概念图版）.html').write_text(h)
    print(c, 'ok', f'{len(probs)} 处定位退回标题' if probs else '', kw)
if missing:
    print('⚠ 以下课程没有生成概念图版（没有右上目录和概念关系图）：', '、'.join(missing))
    print('  概念关系要手工整理：先跑 concept_map.py skeleton "<课程>" 看小节骨架，')
    print('  写 ROOT/制作记录/概念关系/<课程>.txt（格式见 references/adhd-editions.md），再跑 derive.py concept')
