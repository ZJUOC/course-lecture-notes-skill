#!/usr/bin/env python3
"""单本教材（PDF）输入：看目录、按页抽取。依赖 PyMuPDF（fitz）；扫描版检索用 tesseract。
用法：
  textbook.py toc <pdf> [最大层级=3]
      打印页数、是否有文字层（抽 5 页测），以及书签目录（层级、标题、PDF 页码，从 1 起）。
      没有书签时，把前 15 页渲染成图（toc_pages/），读目录页自己定页码，并找出“印刷页码 = PDF 页码 - 偏移”。
  textbook.py pages <pdf> <首页> <末页> <输出目录> [--dpi 110] [--ocr chi_sim+eng]
      PDF 页码（从 1 起，含两端）。输出：
        p0123.png      每页一张图，读正文、公式、图、题干都看图（约 1.5k token/页）
        text_K.txt     有文字层时按约 2.5 万字符分块的文字（只用来检索、摘抄，公式以图为准）
        ocr.txt        无文字层时 tesseract 识别结果，只用于 grep 定位，不要照抄
        index.json     每页的图片、字数，供 contact_sheet.py sheets 做缩略图总览
      裁图另用 --dpi 250 渲染到别的目录（dpi > 150 时不做 OCR），再 contact_sheet.py grid <单页> 定框、crop 裁切。
      --ocr none 跳过 OCR。
"""
import sys, json, subprocess, shutil
from pathlib import Path
import fitz


def has_text(doc):
    n = doc.page_count
    sample = sorted({min(n - 1, int(n * k / 6)) for k in range(1, 6)})
    chars = [len(doc[i].get_text().strip()) for i in sample]
    return sum(c > 200 for c in chars) >= 3, dict(zip([i + 1 for i in sample], chars))


def render(doc, i, out, dpi):
    pix = doc[i].get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    pix.save(out)


def toc(pdf, maxlevel=3):
    doc = fitz.open(pdf)
    ok, sample = has_text(doc)
    print(f'页数 {doc.page_count}  文字层 {"有" if ok else "无（扫描版）"}  抽样字数 {sample}')
    t = doc.get_toc()
    if t:
        for lv, title, page in t:
            if lv <= maxlevel:
                print('  ' * (lv - 1) + f'{title}  ·p{page}')
        return
    d = Path(pdf).with_suffix('').name[:20] + '_toc_pages'
    out = Path.cwd() / d
    out.mkdir(exist_ok=True)
    for i in range(min(15, doc.page_count)):
        render(doc, i, out / f'p{i + 1:04d}.png', 80)
    print(f'没有书签。前 15 页已渲染到 {out}，先看缩略图找目录页，再读目录定页码偏移。')


def pages(pdf, a, b, outdir, dpi=110, lang='chi_sim+eng'):
    doc = fitz.open(pdf)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    ok, _ = has_text(doc)
    items, texts = [], []
    for p in range(a, b + 1):
        f = out / f'p{p:04d}.png'
        render(doc, p - 1, f, dpi)
        tx = doc[p - 1].get_text() if ok else ''
        texts.append((p, tx))
        items.append({'n': p, 'ts': f'p{p}', 'file': f.name, 'chars': len(tx.strip())})
    if ok:
        chunks, cur = [], ''
        for p, tx in texts:
            piece = f'\n\n===== PDF p{p} =====\n{tx}'
            if cur and len(cur) + len(piece) > 25000:
                chunks.append(cur)
                cur = ''
            cur += piece
        chunks.append(cur)
        for k, c in enumerate(chunks):
            (out / f'text_{k}.txt').write_text(c)
        print(f'文字层：{len(chunks)} 块 text_K.txt（约 {sum(map(len, chunks)) // 1000}k 字符）')
    elif dpi > 150 or lang == 'none':
        print('高分辨率渲染（裁图用）：不做 OCR')
    elif shutil.which('tesseract'):
        with open(out / 'ocr.txt', 'w') as fo:
            for it in items:
                r = subprocess.run(['tesseract', str(out / it['file']), '-', '-l', lang, '--psm', '6'],
                                   capture_output=True, text=True)
                fo.write(f'\n\n===== PDF p{it["n"]} =====\n{r.stdout}')
        print('扫描版：ocr.txt 只用于 grep 定位页码；正文、公式一律看页面图')
    else:
        print('扫描版且没有 tesseract：只能看页面图')
    (out / 'index.json').write_text(json.dumps({'pdf': str(Path(pdf).resolve()), 'dpi': dpi, 'items': items}, ensure_ascii=False, indent=0))
    print(f'{b - a + 1} 页图片 → {out}（读一页约 1.5k token；先 contact_sheet.py sheets {out}/index.json 看总览）')


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    opt = {}
    while args and len(args) >= 2 and args[-2].startswith('--'):
        opt[args[-2][2:]] = args[-1]
        args = args[:-2]
    if cmd == 'toc':
        toc(args[0], int(args[1]) if len(args) > 1 else 3)
    elif cmd == 'pages':
        pages(args[0], int(args[1]), int(args[2]), args[3], int(opt.get('dpi', 110)), opt.get('ocr', 'chi_sim+eng'))
    else:
        sys.exit(__doc__)
