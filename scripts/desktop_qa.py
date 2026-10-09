#!/usr/bin/env python3
"""桌面验收：本地起 HTTP 服务（file:// 预览不加载字体图片），用本机 Chrome 检查讲义。
用法：desktop_qa.py <html 文件> <输出目录> [锚点id ...]
检查：1440/1280 宽无横向溢出、MathML 无 merror、图片与字体加载、站内锚点有效、放大框、答案全开/全收；
并对每个锚点截图（已开启 reduced motion，避免平滑滚动造成空白截图）。"""
import sys,json,asyncio,threading,functools,http.server,socketserver,urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
html=Path(sys.argv[1]).resolve();outdir=Path(sys.argv[2]).resolve();outdir.mkdir(parents=True,exist_ok=True);anchors=sys.argv[3:]
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory=str(html.parent)));port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{port}/'+urllib.parse.quote(html.name)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(channel='chrome');pg=await b.new_page(viewport={'width':1440,'height':1000});err=[]
        pg.on('pageerror',lambda e:err.append(str(e)));await pg.emulate_media(reduced_motion='reduce')
        await pg.goto(url);await pg.evaluate('document.fonts.ready');await pg.wait_for_timeout(800)
        r=await pg.evaluate('''()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,mathErrors:document.querySelectorAll('merror').length,figures:document.querySelectorAll('main figure').length,imagesLoaded:[...document.querySelectorAll('main figure img')].every(i=>i.complete&&i.naturalWidth>0),fonts:[...document.fonts].map(f=>f.family+':'+f.status),blocks:document.querySelectorAll('.block').length,details:document.querySelectorAll('details').length,badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).map(a=>a.hash),rawDollar:[...document.querySelectorAll('main p,main li,main td,main figcaption')].filter(e=>/\\$/.test(e.textContent)).length})''')
        await pg.screenshot(path=str(outdir/'top.png'))
        for a in anchors:
            await pg.locator(f'[id="{a}"]').evaluate('e=>e.scrollIntoView({block:"start"})');await pg.wait_for_timeout(150);await pg.screenshot(path=str(outdir/f'{a}.png'))
        if r['figures']:
            await pg.locator('main figure img').first.click();r['lightbox']=await pg.locator('dialog').evaluate('e=>e.open');await pg.locator('dialog .close').click()
        await pg.locator('#toggle').click();r['allExpanded']=await pg.locator('details').evaluate_all('ds=>ds.every(d=>d.open)')
        r['expandedOverflow']=await pg.evaluate('document.documentElement.scrollWidth>innerWidth')
        await pg.locator('#toggle').click();r['allCollapsed']=await pg.locator('details').evaluate_all('ds=>ds.every(d=>!d.open)')
        await pg.set_viewport_size({'width':1280,'height':900});r['narrowDesktop']=await pg.evaluate('({w:innerWidth,sw:document.documentElement.scrollWidth})')
        r['errors']=err;await b.close();return r
r=asyncio.run(main());srv.shutdown()
ok=r['scrollWidth']<=r['width'] and not r['mathErrors'] and r['imagesLoaded'] and all(s.endswith('loaded') for s in r['fonts']) and not r['badAnchors'] and not r['rawDollar'] and r.get('lightbox',True) and r['allExpanded'] and not r['expandedOverflow'] and r['allCollapsed'] and r['narrowDesktop']['sw']<=r['narrowDesktop']['w'] and not r['errors']
r['PASS']=ok;(outdir/'qa.json').write_text(json.dumps(r,ensure_ascii=False,indent=1));print(json.dumps(r,ensure_ascii=False))
