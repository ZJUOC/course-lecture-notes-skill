"""读取 制作记录/概念关系/<课程>.txt（手工整理的概念与依赖），对照讲义 HTML 校验，输出给页面用的 JSON。

格式：
  @小节id
  概念名 | 依赖1:边标签, 依赖2 | 原文定位词 | 一行注解（可省；写了就在正文插概念小标题，见 wisdom.py）
  用到: 概念A, 概念B

用法：python3 concept_map.py            校验全部课程
      python3 concept_map.py skeleton [课程]  打印小节骨架（✓ 表示已整理），用来起草概念关系
"""
import re, json, sys
from pathlib import Path
from bs4 import BeautifulSoup

from common import REC as R, ROOT
SEP = re.compile(r'(?<= )\|(?= |$)')


def parse(path):
    secs, order, cur = {}, [], None
    for ln, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('@'):
            cur = line[1:].strip()
            secs[cur] = {'nodes': [], 'use': []}
            order.append(cur)
            continue
        if cur is None:
            raise ValueError(f'{path.name}:{ln} 在 @小节 之前')
        if line.startswith('用到:'):
            secs[cur]['use'] = [x.strip() for x in line[3:].split(', ') if x.strip()]
            continue
        parts = [p.strip() for p in SEP.split(line)]
        name = parts[0]
        deps = []
        if len(parts) > 1 and parts[1]:
            for d in parts[1].split(', '):
                d = d.strip()
                if ':' in d:
                    n, lab = d.split(':', 1)
                    deps.append([n.strip(), lab.strip()])
                else:
                    deps.append([d, ''])
        loc = parts[2] if len(parts) > 2 and parts[2] else name
        note = parts[3] if len(parts) > 3 else ''
        secs[cur]['nodes'].append({'n': name, 'd': deps, 'at': loc, 'ln': ln, 'note': note})
    return secs, order


def section_text(soup):
    """小节 id → 该小节（到下一个 h2/h3 为止）的纯文本。"""
    out = {}
    main = soup.main
    heads = main.find_all(['h2', 'h3'])
    for h in heads:
        if not h.get('id'):
            continue
        t = []
        for sib in h.find_next_siblings():
            if sib.name in ('h2', 'h3'):
                break
            t.append(sib.get_text(' '))
        out[h['id']] = re.sub(r'\s+', '', ' '.join(t) + h.get_text())
    return out


def build(course):
    src = R / '概念关系' / f'{course}.txt'
    secs, order = parse(src)
    soup = BeautifulSoup((ROOT / f'{course}.html').read_text(), 'html.parser')
    texts = section_text(soup)
    ids = [h.get('id') for h in soup.main.find_all(['h2', 'h3']) if h.get('id')]
    problems, seen = [], set()
    # 按页面中的小节顺序检查依赖是否已经出现过
    for sid in sorted(order, key=lambda s: ids.index(s) if s in ids else 10**6):
        if sid not in texts:
            problems.append(f'找不到小节 #{sid}')
            continue
        s = secs[sid]
        for nd in s['nodes']:
            if nd['n'] in seen:
                problems.append(f'重复概念 {nd["n"]}（第 {nd["ln"]} 行）')
            for d, _ in nd['d']:
                if d not in seen and d not in {x['n'] for x in s['nodes']}:
                    problems.append(f'#{sid} {nd["n"]} 的依赖“{d}”未在前面定义（第 {nd["ln"]} 行）')
            key = re.sub(r'\s+', '', nd['at'])
            if key not in texts[sid]:
                nd['miss'] = 1
                problems.append(f'#{sid} 定位词“{nd["at"]}”不在原文（第 {nd["ln"]} 行），点击时跳到小节标题')
        seen |= {x['n'] for x in s['nodes']}
        for u in s['use']:
            if u not in seen:
                problems.append(f'#{sid} 用到的“{u}”未定义')
    data = {sid: {'nodes': [{'n': x['n'], 'd': x['d'], 'at': x['at']} for x in secs[sid]['nodes']],
                  'use': secs[sid]['use']} for sid in order}
    return data, problems


def skeleton(course, limit=10):
    """省 token：只列出每个小节的 id、标题、加粗词和语义块标题，整理概念关系时看这个，不必读整页 HTML。"""
    soup = BeautifulSoup((ROOT / f'{course}.html').read_text(), 'html.parser')
    src = R / '概念关系' / f'{course}.txt'
    done = set(parse(src)[0]) if src.exists() else set()
    for h in soup.main.find_all(['h2', 'h3']):
        if not h.get('id'):
            continue
        words = []
        for sib in h.find_next_siblings():
            if sib.name in ('h2', 'h3'):
                break
            for el in sib.select('.block-title, strong'):
                for m in el.find_all('math'):
                    ann = m.find('annotation')
                    m.replace_with(ann.get_text() if ann else '')
                w = re.sub(r'\s+', ' ', el.get_text(' ')).strip(' ：:·。')
                if 1 < len(w) <= 40 and w not in words:
                    words.append(w)
        mark = '✓' if h['id'] in done else ' '
        ind = '' if h.name == 'h2' else '  '
        print(f'{mark}{ind}@{h["id"]}  {h.get_text(" ", strip=True)}')
        if words:
            print(f'{ind}     ', ' / '.join(words[:limit]) + (' …' if len(words) > limit else ''))


if __name__ == '__main__':
    from common import COURSES
    if sys.argv[1:2] == ['skeleton']:
        for c in sys.argv[2:] or COURSES:
            print('#', c)
            skeleton(c)
        sys.exit(0)
    bad = 0
    for c in COURSES:
        data, probs = build(c)
        n = sum(len(v['nodes']) for v in data.values())
        e = sum(len(x['d']) for v in data.values() for x in v['nodes'])
        print(f'{c}: {len(data)} 节, {n} 个概念, {e} 条关系, {len(probs)} 个问题')
        for p in probs:
            print('   ', p)
        bad += sum(1 for p in probs if '定位词' not in p)
    sys.exit(1 if bad else 0)
