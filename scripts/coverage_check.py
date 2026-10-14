#!/usr/bin/env python3
"""核对覆盖表：教材的每个例题、习题、定义、定理……都在讲义里有位置，且这个位置真的存在。
用法：coverage_check.py <制作记录.md> <底稿.html>
覆盖表格式见 references/mainlines.md“例题驱动”：表头含“讲义位置”，每行一个教材条目。
讲义位置写块标题的“类别 编号”（例 3、习题 5、P 2、定义 1、定理 2、结论 4）或小节 id（#fermat），可写多个；
“同类：例 6，结论 4”表示没单独讲，但用这些位置就能做出来。
打印 json：rows（按类型计数）、problems（必须为空）；PASS = 没有 problems。
"""
import json, re, sys
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

LABEL = re.compile(r'(例|习题|P|定义|定理|结论)\s*(\d+)')


def table(md):
    """记录里“## 覆盖表”一节的表格 → [(条目, 类型, 位置)]。"""
    sec = re.search(r'^## 覆盖表\s*$(.*?)(?=^## |\Z)', md, re.M | re.S)
    if not sec:
        return None
    rows, head = [], None
    for ln in sec.group(1).splitlines():
        if not ln.strip().startswith('|'):
            continue
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        if head is None:
            head = cells
            continue
        if set(''.join(cells)) <= set('-: '):
            continue
        d = dict(zip(head, cells))
        rows.append((d.get('教材条目', cells[0]), d.get('类型', ''), d.get('讲义位置', '')))
    return rows


def targets(html):
    """讲义里存在的位置：块标题与练习标题的“类别 编号”，以及所有 id。"""
    soup = BeautifulSoup(Path(html).read_text(), 'html.parser')
    m = soup.main
    have = {f'#{t["id"]}' for t in m.find_all(id=True)}
    titles = [t.get_text(' ', strip=True) for t in m.select('.block-title')]
    titles += [h.get_text(' ', strip=True) for h in m.find_all(['h3', 'h4']) if h.get('id', '').startswith('practice-')]
    for t in titles:
        x = re.match(r'(例|习题|P|定义|定理|结论)\s*(\d+)', t)
        if x:
            have.add(f'{x.group(1)} {x.group(2)}')
    return have


def check(record, html):
    rows = table(Path(record).read_text())
    if rows is None:
        return {'PASS': False, 'problems': ['记录里没有“## 覆盖表”一节']}
    have = targets(html)
    probs = []
    for item, kind, loc in rows:
        refs = [f'{a} {b}' for a, b in LABEL.findall(loc)] + re.findall(r'#[A-Za-z0-9_-]+', loc)
        if not loc:
            probs.append(f'没有讲义位置：{item}')
        elif not refs:
            probs.append(f'看不出讲义位置（应写 例 k / 习题 k / 定理 k / #id）：{item} → {loc}')
        for r in refs:
            if r not in have:
                probs.append(f'讲义里找不到 {r}：{item}')
    return {'PASS': not probs and bool(rows), 'rows': len(rows),
            'by_type': dict(Counter(k or '未写类型' for _, k, _ in rows)),
            'same_kind_only': sum(l.startswith('同类') for _, _, l in rows),
            'problems': probs or ([] if rows else ['覆盖表是空的'])}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    r = check(*sys.argv[1:])
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r['PASS'] else 1)
