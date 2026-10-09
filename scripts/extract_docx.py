#!/usr/bin/env python3
"""抽取课堂转写 DOCX：文字 + 全部嵌图（DrawingML blip 与 VML imagedata 都处理），按出现顺序标记。
用法：extract_docx.py <输出目录> <a.docx> [b.docx ...] [--chunk 22000]
输出（每份 docx 一个子目录 <stem>/）：
  images/NNN.jpg        嵌图，按出现顺序编号
  marked.txt            正文，时间戳压缩为 |hh:mm:ss|，图片位置写成 [[IMG NNN @时间戳]]
  chunk_K.txt           marked.txt 按 --chunk 字符切分，便于分段 Read（每段约 1 万 token）
  index.json            每张图的编号、时间戳、sha256；头部三行（课程名/教师/日期）
先看 index.json 的头部核对教师与正文日期，再用 contact_sheet.py 看图。"""
import sys,zipfile,re,json,hashlib
from pathlib import Path
args=sys.argv[1:];chunk=22000
if '--chunk' in args:i=args.index('--chunk');chunk=int(args[i+1]);del args[i:i+2]
out=Path(args[0]);out.mkdir(parents=True,exist_ok=True);summary={}
for f in map(Path,args[1:]):
    z=zipfile.ZipFile(f);x=z.read('word/document.xml').decode()
    rels=dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',z.read('word/_rels/document.xml.rels').decode()))
    d=out/f.stem;(d/'images').mkdir(parents=True,exist_ok=True)
    lines=[];imgs=[];ts='';n=0;head=[]
    for p in re.findall(r'<w:p[ >].*?</w:p>',x,flags=re.S):
        for rid in re.findall(r'(?:r:id|r:embed)="(rId\d+)"',p):
            tgt=rels.get(rid)
            if not tgt or 'media' not in tgt:continue
            n+=1;data=z.read('word/'+tgt.lstrip('/').replace('word/',''));fn=f'{n:03d}'+Path(tgt).suffix
            (d/'images'/fn).write_bytes(data);imgs.append({'n':n,'file':f'images/{fn}','ts':ts,'sha256':hashlib.sha256(data).hexdigest()})
            lines.append(f'[[IMG {n:03d} @{ts}]]')
        t=re.sub(r'<[^>]+>','',p).strip()
        if re.fullmatch(r'\d\d:\d\d:\d\d',t):ts=t;continue
        if t:
            if len(head)<3:head.append(t)
            lines.append(f'|{ts}| {t}' if ts else t)
    s='\n'.join(lines);s=re.sub(r'\n(\|\d\d:\d\d:\d\d\|) ',r' \1 ',s)
    (d/'marked.txt').write_text(s)
    k=0
    for i in range(0,len(s),chunk):(d/f'chunk_{k}.txt').write_text(s[i:i+chunk+200]);k+=1
    info={'source':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'head':head,'chars':len(s),'chunks':k,'images':len(imgs),'unique_images':len({i['sha256'] for i in imgs}),'items':imgs}
    (d/'index.json').write_text(json.dumps(info,ensure_ascii=False,indent=1))
    summary[f.name]={k2:info[k2] for k2 in ('head','chars','chunks','images','unique_images')}
print(json.dumps(summary,ensure_ascii=False,indent=1))
