"""由已构建的讲义生成 ADHD 版：按句子作用分色荧光标注（ThesisGlow 式），并加阅读地图。

用法：python3 make_adhd.py（通常由 derive.py 调用）
输入：ROOT/NN *.html；输出：ROOT/NN *（ADHD版）.html。原讲义不改动。
人工修订：ROOT/制作记录/ADHD标注修订.json，{"句子开头若干字": "none|thesis|claim|evidence|counter|term"}。
"""
import re, json
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

from common import ROOT, REC as R, COURSES
OVERRIDE = R / 'ADHD标注修订.json'
over = json.loads(OVERRIDE.read_text()) if OVERRIDE.exists() else {}

END = re.compile(r'([。！？；!?]+[”’」）)]*)')
CUES = [  # 优先级从高到低
    ('counter', re.compile(r'注意|不能|不可(?!能)|不要|别把|易错|出错|错误|写错|弄错|反例|不成立|误以为|误认为|失效|陷阱|不一定|并非|而不是|不等于|不能直接')),
    ('thesis', re.compile(r'^(可见|这说明|这表明|也就是说|换句话说|总之|归纳起来|结论是|一句话|由此可见|这就是说|所以说)|核心|本质|关键在于|最重要')),
    ('claim', re.compile(r'思路|方法是|办法是|关键是|第一步|先.{1,24}再|只需|只要.{0,24}就|可以用|改用|转化为|化成|化为|入口|策略|技巧|步骤')),
    ('evidence', re.compile(r'^(例如|比如|譬如|举个例子)|例如')),
]
TASK = re.compile(r'求|计算|证明|判断|写出|讨论|化成|解方程|说明|比较|？|\\?')
BLOCK_CAT = {'definition': 'term', 'theorem': 'thesis', 'result': 'thesis', 'warning': 'counter'}


def is_display(node):
    return isinstance(node, Tag) and (('math' in node.get('class', []) and 'display' in node.get('class', []))
                                      or (node.name == 'math' and node.get('display') == 'block'))


def plain(nodes):
    out = []
    for n in nodes:
        if isinstance(n, NavigableString):
            out.append(str(n))
        elif n.name == 'math' or n.find('math') is not None and n.name not in ('strong', 'em', 'a'):
            out.append('□')
        else:
            out.append(n.get_text())
    return re.sub(r'\s+', '', ''.join(out))


def context(p):
    blk = p.find_parent('div', class_='block')
    kind = None
    if blk:
        kind = next((c for c in blk['class'] if c != 'block'), None)
    return kind, blk, p.find_parent('details') is not None


def classify(text, kind, blk, in_details, p):
    for k, v in over.items():
        if text.startswith(k):
            return None if v == 'none' else v
    if len(text) < 6:
        return None
    if in_details:
        return 'counter' if CUES[0][1].search(text) else None
    if kind == 'warning':
        # 易错块：只标第一句（易错点本身）和带否定、提醒语气的句子
        if not blk.get('data-adhd-first'):
            blk['data-adhd-first'] = '1'
            return 'counter'
        return 'counter' if CUES[0][1].search(text) else None
    if kind in BLOCK_CAT:
        return BLOCK_CAT[kind]
    if kind in ('example', 'question'):
        # 题目本身（标题后的第一段）标为例子；解答中只标易错与方法
        body = [x for x in blk.find_all(['p', 'li'], recursive=True)
                if 'block-title' not in x.get('class', []) and not x.find_parent('details')]
        if body and body[0] is p and not blk.get('data-adhd-task'):
            # 题目段：标到第一个提出任务的句子为止，后面的解答不标
            if TASK.search(text):
                blk['data-adhd-task'] = '1'
            return 'evidence'
        for cat, rx in (CUES[0], CUES[2]):
            if rx.search(text):
                return cat
        return None
    for cat, rx in CUES:
        if rx.search(text):
            return cat
    return None


def sentences(p):
    """把段落子节点切成句子组；行间公式单独成组且不参与标注。"""
    groups, cur = [], []
    for node in list(p.contents):
        if is_display(node):
            if cur: groups.append(cur); cur = []
            groups.append([node]); continue
        if isinstance(node, NavigableString):
            parts = END.split(str(node))
            # parts: 文本, 分隔符, 文本, 分隔符, ...
            for i in range(0, len(parts), 2):
                piece = parts[i] + (parts[i + 1] if i + 1 < len(parts) else '')
                if not piece:
                    continue
                cur.append(NavigableString(piece))
                if i + 1 < len(parts):
                    groups.append(cur); cur = []
            node.extract()
        else:
            cur.append(node.extract())
    if cur: groups.append(cur)
    return groups


def process(path_in, path_out, stats):
    soup = BeautifulSoup(path_in.read_text(), 'html.parser')
    main = soup.main
    n = 0
    for p in main.find_all(['p', 'li']):
        if 'block-title' in p.get('class', []) or p.find(['p', 'ul', 'ol', 'div']):
            continue
        kind, blk, in_details = context(p)
        groups = sentences(p)
        for g in groups:
            if len(g) == 1 and is_display(g[0]):
                p.append(g[0]); continue
            text = plain(g)
            cat = classify(text, kind, blk, in_details, p)
            if cat:
                m = soup.new_tag('mark', attrs={'class': f'hl hl-{cat}', 'data-cat': cat, 'id': f'hl-{n}'})
                n += 1
                for x in g: m.append(x)
                p.append(m)
                stats[cat] = stats.get(cat, 0) + 1
                stats.setdefault('_samples', {}).setdefault(cat, []).append(text[:70])
            else:
                for x in g: p.append(x)
    # 正文中的加粗术语
    for s in main.find_all('strong'):
        if s.find_parent(class_='block-title') or s.find_parent('details') or s.find_parent('mark') \
                or s.find_parent(['h1', 'h2', 'h3', 'h4', 'th']) or len(s.get_text(strip=True)) > 16 \
                or (s.parent and s.parent.get_text(strip=True) == s.get_text(strip=True)):
            continue
        s['class'] = s.get('class', []) + ['kt']
        s['data-cat'] = 'term'
        s['id'] = f'hl-{n}'; n += 1
        stats['term'] = stats.get('term', 0) + 1
    head = soup.head
    import hashlib
    ver = hashlib.sha1((ROOT/'ADHD工具/adhd.css').read_bytes()+(ROOT/'ADHD工具/adhd.js').read_bytes()).hexdigest()[:8]
    head.append(soup.new_tag('link', rel='stylesheet', href=f'ADHD工具/adhd.css?v={ver}'))
    t = soup.title
    t.string = t.get_text() + '（ADHD版）'
    soup.body.append(soup.new_tag('script', src=f'ADHD工具/adhd.js?v={ver}'))
    for b in main.find_all(attrs={'data-adhd-first': True}): del b['data-adhd-first']
    for b in main.find_all(attrs={'data-adhd-task': True}): del b['data-adhd-task']
    path_out.write_text(str(soup))
    return n


if __name__ == '__main__':
    report = {}
    for c in COURSES:
        src = ROOT / f'{c}.html'
        dst = ROOT / f'{c}（ADHD版）.html'
        st = {}
        n = process(src, dst, st)
        samples = st.pop('_samples', {})
        report[c] = {'total': n, **st, 'samples': samples}
        print(c, n, {k: v for k, v in st.items()})
    (R / 'ADHD标注报告.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
