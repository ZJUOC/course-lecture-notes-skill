#!/usr/bin/env python3
"""把一批图片拼成带编号的缩略图总览，一次 Read 看 20 张（约 1.5k token/张总览）。
用法：
  contact_sheet.py sheets <index.json 或图片目录> <输出前缀>        # 4×5 总览，标注 编号+时间戳
  contact_sheet.py grid <输出.png> <图1> [图2 ...]                   # 叠加 100px 坐标网格（按原图坐标标注），2 列拼图，用来确定裁切框；只给一张图时输出 1500px，看得更清楚
  contact_sheet.py crop <spec.json> <输出目录>                        # 按 {"名称":["源图",[x0,y0,x1,y1]],...} 裁切，并写 裁切清单.json
PDF 页面先用：pdftoppm -r 100 -f P -l P -png file.pdf out   （裁图时用 -r 250，坐标 ×2.5）"""
import sys,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
cmd=sys.argv[1]
if cmd=='sheets':
    src=Path(sys.argv[2]);pre=sys.argv[3]
    if src.suffix=='.json':
        idx=json.load(open(src));items=[(src.parent/i['file'],f"{i['n']} {i['ts']}") for i in idx['items']]
    else:items=[(p,p.name) for p in sorted(src.iterdir()) if p.suffix.lower() in ('.jpg','.jpeg','.png')]
    for s in range(0,len(items),20):
        sh=Image.new('RGB',(4*480,5*290),'white');dr=ImageDraw.Draw(sh)
        for k,(p,lab) in enumerate(items[s:s+20]):
            im=Image.open(p).convert('RGB');im.thumbnail((470,265));X,Y=(k%4)*480,(k//4)*290
            sh.paste(im,(X,Y+20));dr.text((X+4,Y+2),lab,fill='red')
        out=f'{pre}_{s//20}.jpg';sh.save(out,quality=82);print(out)
elif cmd=='grid':
    out=sys.argv[2];ims=[]
    for p in sys.argv[3:]:
        im=Image.open(p).convert('RGB');dr=ImageDraw.Draw(im);W,H=im.size
        side=1500 if len(sys.argv)==4 else 900   # 单张图时输出更大；标签字号随原图尺寸放大，缩小后仍看得清
        fnt=ImageFont.load_default(size=max(12,int(max(W,H)/side*13)))
        for x in range(0,W,100):dr.line([(x,0),(x,H)],fill=(255,120,120));dr.text((x+2,2),str(x),fill='red',font=fnt)
        for y in range(0,H,100):dr.line([(0,y),(W,y)],fill=(255,120,120));dr.text((2,y+2),str(y),fill='red',font=fnt)
        dr.text((W//2,4),Path(p).name,fill='blue',font=fnt);im.thumbnail((side,side));ims.append(im)
    w=max(i.size[0] for i in ims);h=max(i.size[1] for i in ims);rows=(len(ims)+1)//2
    sh=Image.new('RGB',(2*w,rows*h),'white')
    for k,im in enumerate(ims):sh.paste(im,((k%2)*w,(k//2)*h))
    sh.save(out);print(out,'（网格标注是原图像素坐标）')
elif cmd=='crop':
    spec=json.load(open(sys.argv[2]));od=Path(sys.argv[3]);od.mkdir(parents=True,exist_ok=True);rec={}
    for name,(src,box) in spec.items():
        c=Image.open(src).convert('RGB').crop(tuple(box));c.save(od/f'{name}.png',optimize=True);rec[name]={'source':src,'crop_box':box,'size':c.size}
    (od/'裁切清单.json').write_text(json.dumps(rec,ensure_ascii=False,indent=1));print(len(rec),'crops')
