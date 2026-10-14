#!/usr/bin/env python3
"""检查讲义 HTML 是否符合“不随主线变化的格式”（references/mainlines.md 末尾），并给出结构画像。
用法：
  format_check.py <底稿或页面.html>            打印 json：errors（必须为空）、warnings、profile；PASS = 没有 errors
  format_check.py a.html b.html c.html        多份对照：逐项列出画像，看不同代理/不同次写出的讲义格式是否一致
errors 是结构问题（缺学习路线、块没有标题、Markdown 没转换干净……），warnings 是写法偏差（例题标题格式、id 用中文……）。
"""
import json, re, sys
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

norm = lambda h: re.sub(r'\s+', ' ', h.get_text(' ')).strip()
KINDS = {'definition', 'theorem', 'result', 'example', 'warning', 'question'}
ABBR = {'definition': 'D', 'theorem': 'T', 'result': 'R', 'example': 'E', 'warning': 'W', 'question': 'Q'}


def check(path):
    soup = BeautifulSoup(Path(path).read_text(), 'html.parser')
    m = soup.main
    E, W = [], []
    h1 = m.find_all('h1')
    if len(h1) != 1:
        E.append(f'h1 应恰好 1 个，实际 {len(h1)}')
    else:
        p = h1[0].find_next_sibling('p')
        if not (p and p.strong and p.get_text().strip() == p.strong.get_text().strip()):
            E.append('h1 后第一段应是单独一行加粗的“课程 · 讲义说明（范围）”')
        elif not re.search(r' · .*学习讲义（.+）$', re.sub(r'\s+', ' ', p.get_text()).strip()):
            W.append('加粗来源行应写成“课程 · 教师课程学习讲义（范围）”或“课程 · 《书名》学习讲义（范围）”')
    h2s = m.find_all('h2')
    route = [h for h in h2s if h.get_text().strip() == '学习路线']
    if not route:
        E.append('缺少 ## 学习路线')
    elif not any(n.name == 'table' for n in route[0].find_next_siblings() if n.find_previous('h2') is route[0]):
        E.append('学习路线下没有表格')
    if h2s and h2s[0] not in route:
        E.append('第一个 h2 应是 学习路线')
    intro = [n for n in (h1[0].find_next_siblings() if h1 else []) if n.find_previous('h2') is None and n.name == 'p']
    if len(intro) < 2:
        W.append('h1 后缺少导言段落')
    units = [h for h in h2s if h not in route]
    for h in units:
        t = norm(h)
        if not re.match(r'\d+ \S', t):
            E.append(f'单元标题应以“N ”开头：{t[:20]}')
    h3s = m.find_all('h3')
    practice = [h for h in m.find_all(['h3', 'h4']) if h.get('id', '').startswith('practice-')]
    for h in h3s:
        t = norm(h)
        if h in practice:
            continue
        if re.match(r'[A-Z]\d+ \S', t):
            W.append(f'题目式小节建议用 id=practice-…，才会装进练习块：{t[:20]}')
        elif not re.match(r'\d+\.\d+ \S', t):
            E.append(f'小节标题应以“N.M ”开头（练习写 ### P1 … {{#practice-p1}}）：{t[:20]}')
    if not practice:
        E.append('没有练习（### P1 … 或 #### 习题 k … {#practice-…}）')
    for h in practice:
        if h.get('id') == 'practice-concepts':
            continue
        sib = []
        for n in h.find_next_siblings():
            if n.name in ('h2', 'h3', 'h4'):
                break
            sib.append(n)
        if not any(n.name == 'details' or n.find('details') for n in sib):
            E.append(f'练习没有折叠的提示/解析：{h.get_text(strip=True)[:20]}')
    if not m.find(id='practice-concepts'):
        W.append('缺少 ### C 概念检查 {#practice-concepts}')
    blocks = m.select('div.block')
    ex_titles = []
    for b in blocks:
        kind = [c for c in b['class'] if c != 'block']
        if not kind or kind[0] not in KINDS:
            E.append(f'未知的块类型：{kind}')
            continue
        tt = b.find(class_='block-title')
        if not tt:
            E.append(f'{kind[0]} 块缺少加粗标题行：{b.get_text(" ", strip=True)[:30]}')
            continue
        title = norm(tt)
        if kind[0] == 'example' and not title.startswith('练习'):
            ex_titles.append(title)
            if not re.match(r'(例|变式)\s*\d+(\.\d+)?\s*·\s*\S', title):
                W.append(f'例题标题建议写成“例 k · 对象与所求量”：{title[:24]}')
            body = len(b.get_text(strip=True)) - len(tt.get_text(strip=True))
            if body < 60:
                W.append(f'例题内容过短（可能没写解答）：{title[:24]}')
        if not title.startswith('练习') and not re.search(r'·\s*\S', title):
            W.append(f'块标题建议写成“类别 · 名称”：{title[:24]}')
    dup = [t for t, k in Counter(re.sub(r'^(例|变式)\s*\d*\s*', '', t) for t in ex_titles).items() if k > 1]
    if dup:
        W.append(f'例题标题重复：{dup[:3]}')
    text = m.get_text(' ')
    for pat, name in ((r':::', '没转换的 :::'), (r'\*\*', '没转换的 **'), (r'(?<!\\)\$', '没转换的 $')):
        if re.search(pat, text):
            E.append(f'正文里有{name}')
    for f in m.find_all('figure'):
        if not f.find('figcaption') or not f.figcaption.get_text(strip=True):
            E.append('图缺少图注')
        src = (f.find('img') or {}).get('src', '')
        if not src.startswith('资源/') and not src.startswith('data:'):
            W.append(f'图片路径应在 资源/ 下：{src}')
    # 画像：每个 N.M 小节里语义块的顺序，看主线是否贯彻
    seqs = []
    for h in h3s:
        if h in practice:
            continue
        s = ''
        for n in h.find_next_siblings():
            if n.name in ('h2', 'h3'):
                break
            for b in ([n] if 'block' in (n.get('class') or []) else n.select('div.block') if hasattr(n, 'select') else []):
                if norm(b.find(class_='block-title') or b).startswith('练习'):
                    continue
                s += ABBR.get([c for c in b['class'] if c != 'block'][0], '?')
        seqs.append(s)
    nonempty = [s for s in seqs if s]
    kinds = Counter(c for b in blocks for c in b['class'] if c in KINDS)
    prof = {
        'units': len(units), 'sections': len(seqs), 'practice': len([h for h in practice if h.get('id') != 'practice-concepts']),
        'section_practice': len([h for h in practice if h.name == 'h4']),
        'concept_check': bool(m.find(id='practice-concepts')), 'blocks': dict(sorted(kinds.items())),
        'examples_per_section': round(kinds.get('example', 0) / max(1, len(seqs)), 2),
        'example_first': round(sum(s[0] == 'E' for s in nonempty) / max(1, len(nonempty)), 2),
        'definition_first': round(sum(s[0] == 'D' for s in nonempty) / max(1, len(nonempty)), 2),
        'section_patterns': Counter(seqs).most_common(4),
        'figures': len(m.find_all('figure')), 'tables': len(m.find_all('table')), 'math': len(m.find_all('math')),
        'details': len(m.find_all('details')), 'chars': len(text),
        'ascii_ids': round(sum(bool(re.fullmatch(r'[a-z0-9-]+', h.get('id', ''))) for h in units + h3s) / max(1, len(units + h3s)), 2),
        'example_title_style': Counter('例 k · …' if re.match(r'(例|变式)\s*\d', t) else '例题 · …' if t.startswith('例题') else '其他' for t in ex_titles),
    }
    groups = {}
    for w in W:
        k, _, v = w.partition('：')
        groups.setdefault(k, []).append(v)
    W2 = [f'{k}（{len(v)} 处）' + (f'：{"；".join(v[:3])}' if v[0] else '') for k, v in groups.items()]
    return {'file': str(path), 'PASS': not E, 'errors': E, 'warnings': W2, 'warning_count': len(W), 'profile': prof}


if __name__ == '__main__':
    rs = [check(p) for p in sys.argv[1:]]
    if len(rs) == 1:
        print(json.dumps(rs[0], ensure_ascii=False, indent=1, default=str))
        sys.exit(0 if rs[0]['PASS'] else 1)
    keys = list(rs[0]['profile'])
    w = 22
    print(' ' * 22 + ''.join(Path(r['file']).stem[:w - 2].ljust(w) for r in rs))
    print('PASS'.ljust(22) + ''.join(str(r['PASS']).ljust(w) for r in rs))
    print('errors/warnings'.ljust(22) + ''.join(f"{len(r['errors'])}/{r['warning_count']}".ljust(w) for r in rs))
    for k in keys:
        print(k.ljust(22) + ''.join(str(r['profile'][k]).ljust(w) for r in rs))
    for r in rs:
        if r['errors']:
            print('\n' + Path(r['file']).name, 'errors:', *r['errors'][:8], sep='\n  ')
