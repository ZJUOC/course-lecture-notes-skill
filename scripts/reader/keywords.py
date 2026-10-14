"""词语荧光：在正文段落里给句子骨架词（主题、转折对比、结论）加一道醒目的荧光，帮助跳读。

数据：ROOT/制作记录/词语荧光/<课程>.txt，每行“段落开头若干字 || 词1 | 词2”，按页面顺序手工挑选。
匹配：从上一行匹配到的段落往后找，含该前缀、且所有词都在段内文字中的第一段。
已经加粗的词不再加；跨公式的词加不上，会列出来。
derive.py 生成页面时自动调用 apply()；样式（荧光颜色 / 加粗 / 加大 / 关闭）在 reader.css、reader.js，读者在页面左下“词”按钮里选。
单独校验：python3 keywords.py [课程...]，只打印统计和问题，不写文件。
"""
import re, sys
from bs4 import BeautifulSoup, NavigableString
from common import REC

def plain(p):
    out = []
    for n in p.descendants:
        if isinstance(n, NavigableString) and not n.find_parent('math'):
            out.append(str(n))
        elif getattr(n, 'name', None) == 'math':
            a = n.find('annotation')
            out.append('$' + (a.get_text() if a else '') + '$')
    return re.sub(r'\s+', '', ''.join(out))


def wrap(p, soup, word):
    pat = re.compile(r'\s*'.join(map(re.escape, re.sub(r'\s+', '', word))))
    for t in list(p.find_all(string=True)):
        if t.find_parent(['math', 'strong']) or t.find_parent('mark', class_='kw'):
            continue
        s = str(t)
        m = pat.search(s)
        if m:
            k = soup.new_tag('mark', attrs={'class': 'kw'})
            k.string = m.group()
            t.replace_with(NavigableString(s[:m.start()]), k, NavigableString(s[m.end():]))
            return True
    return False


def apply(soup, course):
    src = REC / '词语荧光' / f'{course}.txt'
    paras = [p for p in soup.main.find_all(['p', 'li'])
             if not p.find_parent(['figcaption', 'table', 'nav']) and not p.find(['p', 'li'])]
    texts = [plain(p) for p in paras]
    pos, done, bold, miss = 0, 0, 0, []
    for ln, raw in enumerate(src.read_text().splitlines(), 1):
        if not raw.strip() or raw.startswith('#'):
            continue
        pre, _, ws = raw.partition('||')
        pre = re.sub(r'\s+', '', pre)
        words = [w.strip() for w in ws.split('|') if w.strip()]
        hit = next((i for i in range(pos, len(paras)) if pre in texts[i]
                    and all(re.sub(r'\s+', '', w) in texts[i] for w in words)), None)
        if hit is None:
            miss.append(f'第 {ln} 行找不到段落：{raw[:50]}')
            continue
        pos = hit + 1
        for w in words:
            if wrap(paras[hit], soup, w):
                done += 1
            elif any(re.sub(r'\s+', '', w) in re.sub(r'\s+', '', s.get_text()) for s in paras[hit].find_all('strong')):
                bold += 1
            else:
                miss.append(f'第 {ln} 行“{w}”跨公式，未加')
    return done, bold, miss


if __name__ == '__main__':
    from highlight import highlighted
    for course in sys.argv[1:] or sorted(f.stem for f in (REC / '词语荧光').glob('*.txt')):
        soup = highlighted(course)
        done, bold, miss = apply(soup, course)
        print(course, f'标了 {done} 处，{bold} 处原本已加粗', f'{len(miss)} 个问题')
        for m in miss:
            print('  ', m)
