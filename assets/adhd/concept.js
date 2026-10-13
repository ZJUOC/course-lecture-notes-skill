/* ADHD 概念图版：右上是目录 + 概念关系图（手工整理，数据在页面内 #concept-data），右下留给手写笔记窗口。
   荧光标注样式沿用 adhd.css。 */
(()=>{
const KEY='adhd-concept:'+location.pathname;
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}};
const save=s=>{try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}};
// 手写区默认尺寸：生成时从 Trackpad Studio 手写小窗读出（data-ink），拖过紫点（cal）才用自己存的尺寸
const CD=document.getElementById('concept-data');
const DEF=((CD.dataset.ink||'').match(/^(\d+)x(\d+)$/)||[0,750,470]).slice(1).map(Number);
const st=Object.assign({off:[],ink:true},load());
if(!st.cal){st.iw=DEF[0];st.ih=DEF[1]}
const root=document.documentElement,main=document.querySelector('main');
const DATA=JSON.parse(CD.textContent);
const CATS=[['thesis','结论'],['claim','方法'],['evidence','例子'],['counter','易错'],['term','概念']];
const norm=s=>s.replace(/\s+/g,'');
const txt=el=>{const c=el.cloneNode(true);c.querySelectorAll('math').forEach(m=>{const a=m.querySelector('annotation');m.replaceWith(a?a.textContent:'')});return c.textContent.replace(/\s+/g,' ').trim()};
const vis=el=>{const c=el.cloneNode(true);c.querySelectorAll('annotation').forEach(a=>a.remove());return c.textContent.replace(/\s+/g,' ').trim()};
root.classList.add('cmap-on');

/* 1. 标题与小节范围 */
const heads=[...main.querySelectorAll('h2[id],h3[id]')];
const secOf=new Map();   // 概念名 → 小节 id
for(const [sid,s] of Object.entries(DATA))for(const n of s.nodes)secOf.set(n.n,sid);
const chapters=[];
for(const h of heads){if(h.tagName==='H2'||!chapters.length)chapters.push({h,subs:[]});else chapters[chapters.length-1].subs.push(h)}
const chapOf=new Map();chapters.forEach((c,i)=>{chapOf.set(c.h,i);c.subs.forEach(s=>chapOf.set(s,i))});
function range(sid){const h=document.getElementById(sid);const out=[];let n=h&&h.nextElementSibling;
  while(n&&!/^H[23]$/.test(n.tagName)){out.push(n);n=n.nextElementSibling}return [h,out]}
function locate(sid,word){
  const [h,els]=range(sid);if(!h)return null;const w=norm(word);
  for(const sel of ['strong','.block-title','mark','li','p','figcaption','td']){
    for(const e of els){const cands=e.matches(sel)?[e,...e.querySelectorAll(sel)]:e.querySelectorAll(sel);
      for(const c of cands)if(norm(txt(c)).includes(w)||norm(vis(c)).includes(w))return c}}
  return h;
}
function jump(el){if(!el)return;const d=el.closest('details');if(d)d.open=true;
  el.scrollIntoView({behavior:'smooth',block:/^H/.test(el.tagName)?'start':'center'});
  el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1600)}
const goConcept=name=>{const hd=[...main.querySelectorAll('.cpt-head')].find(e=>e.dataset.c===name);if(hd)return jump(hd);const sid=secOf.get(name);if(!sid)return;const n=DATA[sid].nodes.find(x=>x.n===name);jump(locate(sid,n.at))};

/* 2. 面板骨架 */
const box=document.createElement('div');box.id='cmap';
box.innerHTML=`<nav class="toc" aria-label="目录"><a class="back" href="开始阅读.html">← 课程讲义</a><div class="tl"></div></nav>
<section class="map" aria-label="概念关系"><header><b>概念关系</b><span class="chap"></span>
<button class="inkbtn" title="给右下角手写窗口留位置">手写区</button></header>
<div class="body"></div><footer><span class="dots"></span><span class="hint">A → B：B 用到 A</span></footer></section>`;
const zone=document.createElement('div');zone.id='ink-zone';
zone.innerHTML='<span>手写笔记窗口</span><i class="grip" title="拖动对齐手写窗口的左上角；双击恢复默认"></i>';
document.body.append(box,zone);
/* 智慧区（可选）：每个单元一棵括号树，在右下显示；打开手写区时收起 */
const WD=document.getElementById('wisdom-data'),WZ=WD?JSON.parse(WD.textContent):null;let wzBody=null,wzCur;
if(WZ){root.classList.add('wz-on');const w=document.createElement('div');w.id='wisdom';
  w.innerHTML='<header><b>智慧</b><span>这一单元的大局，打开手写区时收起</span></header><div class="body"></div>';
  document.body.append(w);wzBody=w.querySelector('.body')}
function wisdom(id){if(!wzBody||id===wzCur)return;wzCur=id;const u=WZ[id];
  wzBody.innerHTML=u?(u.path?'<div class="wz-path">'+u.path+'</div>':'')+u.html:'<p class="empty">这一单元还没有整理。</p>';wzBody.scrollTop=0}
const tl=box.querySelector('.tl'),body=box.querySelector('.body'),chapLab=box.querySelector('.chap');
const back=document.querySelector('aside a[href]');if(back)box.querySelector('.back').href=back.getAttribute('href');

/* 3. 目录 */
const tocItems=new Map();
for(const c of chapters){
  const a=document.createElement('a');a.href='#'+c.h.id;a.className='c';a.textContent=txt(c.h);tl.append(a);tocItems.set(c.h,a);
  const sub=document.createElement('div');sub.className='subs';a.after(sub);a.sub=sub;
  for(const s of c.subs){const b=document.createElement('a');b.href='#'+s.id;b.className='s';b.textContent=txt(s);sub.append(b);tocItems.set(s,b)}
}
tl.addEventListener('click',e=>{const a=e.target.closest('a');if(!a)return;e.preventDefault();jump(document.getElementById(decodeURIComponent(a.hash.slice(1))))});

/* 4. 概念图 */
const chip=(name,cls)=>{const b=document.createElement('button');b.className='nd '+(cls||'');b.textContent=name;b.onclick=e=>{e.stopPropagation();goConcept(name)};return b};
function graph(sid){
  const s=DATA[sid],wrap=document.createElement('div');wrap.className='graph';
  const inner=new Set(s.nodes.map(n=>n.n)),layer=new Map();
  const L=n=>{if(layer.has(n.n))return layer.get(n.n);layer.set(n.n,0);
    let v=0;for(const [d] of n.d)if(inner.has(d))v=Math.max(v,1+L(s.nodes.find(x=>x.n===d)));layer.set(n.n,v);return v};
  s.nodes.forEach(L);
  const rows=[];for(const n of s.nodes){const l=layer.get(n.n);(rows[l]=rows[l]||[]).push(n)}
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');wrap.append(svg);
  const el=new Map();
  for(const r of rows){if(!r)continue;const row=document.createElement('div');row.className='row';
    for(const n of r){const cell=document.createElement('div');cell.className='cell';const b=chip(n.n,'cur');cell.append(b);el.set(n.n,b);
      const ext=n.d.filter(([d])=>!inner.has(d));
      if(ext.length){const x=document.createElement('div');x.className='ext';x.append('← ');
        ext.forEach(([d,lab],i)=>{if(i)x.append('、');const a=document.createElement('button');a.textContent=d;a.title=lab||'';a.onclick=e=>{e.stopPropagation();goConcept(d)};x.append(a)});cell.append(x)}
      row.append(cell)}
    wrap.append(row)}
  // 内部依赖画箭头
  wrap.draw=()=>{const W=wrap.getBoundingClientRect();svg.setAttribute('width',W.width);svg.setAttribute('height',W.height);svg.innerHTML='<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="#9b87c9"/></marker></defs>';
    for(const n of s.nodes)for(const [d,lab] of n.d){if(!inner.has(d))continue;
      const a=el.get(d).getBoundingClientRect(),ac=el.get(d).parentNode.getBoundingClientRect(),b=el.get(n.n).getBoundingClientRect();
      let x1=a.left+a.width/2-W.left,y1=ac.bottom-W.top+1,x2=b.left+b.width/2-W.left,y2=b.top-W.top-2;
      if(Math.abs(a.top-b.top)<4){y1=a.top+a.height/2-W.top;y2=y1;x1=a.right-W.left;x2=b.left-W.left-2}
      const p=document.createElementNS('http://www.w3.org/2000/svg','path');
      const my=(y1+y2)/2;p.setAttribute('d',Math.abs(y1-y2)<1?`M${x1},${y1}L${x2},${y2}`:`M${x1},${y1}C${x1},${my} ${x2},${my} ${x2},${y2}`);
      p.setAttribute('marker-end','url(#ah)');svg.append(p);
      if(lab){const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',(x1+x2)/2+4);t.setAttribute('y',(y1+y2)/2+4);t.textContent=lab;svg.append(t)}}};
  return wrap;
}
let shownChap=-1,curSid=null,curGraph=null;
function renderChap(i){
  shownChap=i;body.textContent='';const c=chapters[i];chapLab.textContent=txt(c.h);
  for(const h of [c.h,...c.subs]){const s=DATA[h.id];if(!s||(!s.nodes.length&&!s.use.length))continue;
    const sec=document.createElement('div');sec.className='sec';sec.dataset.sid=h.id;
    const t=document.createElement('button');t.className='st';t.textContent=h===c.h?'本章导入':txt(h);t.onclick=()=>jump(h);sec.append(t);
    const brief=document.createElement('div');brief.className='brief';
    if(s.nodes.length)s.nodes.forEach(n=>brief.append(chip(n.n)));
    else{brief.classList.add('use');brief.append('用到 ');s.use.forEach(u=>brief.append(chip(u)))}
    sec.append(brief);body.append(sec)}
  if(!body.children.length)body.innerHTML='<p class="empty">这一章没有需要单独梳理的概念。</p>';
  curGraph=null;mark(curSid,true);
}
function mark(sid,force){
  if(sid===curSid&&!force)return;curSid=sid;
  body.querySelectorAll('.sec').forEach(sec=>{
    const on=sec.dataset.sid===sid;sec.classList.toggle('cur',on);
    const g=sec.querySelector('.graph');if(g&&!on)g.remove();
    if(on&&!g&&DATA[sid].nodes.length){curGraph=graph(sid);sec.append(curGraph);setTimeout(()=>curGraph&&curGraph.draw(),0)}});
  const c=body.querySelector('.sec.cur');if(c){const r=c.getBoundingClientRect(),R=body.getBoundingClientRect();if(r.top<R.top||r.bottom>R.bottom)body.scrollTop+=r.top-R.top-6}
}
new ResizeObserver(()=>curGraph&&curGraph.draw()).observe(body);

/* 5. 跟随阅读位置 */
function spy(){
  let h=heads[0];for(const x of heads){if(x.getBoundingClientRect().top<160)h=x;else break}
  const i=chapOf.get(h);if(i!==shownChap)renderChap(i);wisdom(chapters[i].h.id);
  // 当前小节：本身有数据就用它，否则退到本章导入
  mark(DATA[h.id]?h.id:chapters[i].h.id);
  tocItems.forEach((a,k)=>a.classList.toggle('on',k===h||k===chapters[i].h));
  tl.querySelectorAll('.subs').forEach(s=>s.classList.toggle('open',s===tocItems.get(chapters[i].h).sub));
  const a=tocItems.get(h);if(a){const r=a.getBoundingClientRect(),R=tl.getBoundingClientRect();if(r.top<R.top||r.bottom>R.bottom)tl.scrollTop+=r.top-R.top-R.height/3}
}
let tick=false;addEventListener('scroll',()=>{if(!tick){tick=true;setTimeout(()=>{tick=false;spy()},60)}},{passive:true});
// 平滑滚动结束、页面加载完（图片撑开高度）后再校正一次
addEventListener('scrollend',spy);addEventListener('load',()=>setTimeout(spy,50));

/* 6. 荧光开关、手写区 */
const dots=box.querySelector('.dots');
for(const [c,n] of CATS){const b=document.createElement('button');b.className='dot hl-'+c;b.dataset.c=c;b.textContent=n;b.title='开关'+n+'荧光';
  b.onclick=()=>{const i=st.off.indexOf(c);i<0?st.off.push(c):st.off.splice(i,1);apply()};dots.append(b)}
/* 词语荧光（mark.kw 手工挑选的句子骨架词；mark.kw2 按分句自动补的浅一档荧光）：可选荧光颜色，或只加粗、加大，或关闭；“密”按钮开关 kw2 */
const KW=[['amber','琥珀'],['coral','橙红'],['green','青绿'],['blue','天蓝'],['pink','粉紫'],['bold','加粗'],['big','加大'],['off','关闭']];
const hasKw=!!document.querySelector('main mark.kw, main mark.kw2'),hasKw2=!!document.querySelector('main mark.kw2');
if(hasKw){
  const w=document.createElement('span');w.className='kwpick';
  w.innerHTML='<button class="kwbtn" title="词语荧光样式">词</button><span class="kwmenu" hidden></span>';
  const menu=w.querySelector('.kwmenu');
  for(const [k,n] of KW){const b=document.createElement('button');b.dataset.k=k;b.className='kwopt kw-'+k;b.textContent=n;
    b.onclick=()=>{st.kw=k;menu.hidden=true;apply()};menu.append(b)}
  w.querySelector('.kwbtn').onclick=e=>{e.stopPropagation();menu.hidden=!menu.hidden};
  document.addEventListener('click',e=>{if(!w.contains(e.target))menu.hidden=true});
  if(hasKw2){const b=document.createElement('button');b.className='kwdbtn';b.textContent='密';
    b.title='密集荧光：每句隔几个词自动补一处浅荧光（点一下开关）';
    b.onclick=()=>{st.kwd=st.kwd==='sparse'?'dense':'sparse';apply()};w.append(b)}
  dots.prepend(w);
}
function apply(){
  for(const [c] of CATS)root.classList.toggle('off-'+c,st.off.includes(c));
  if(hasKw){const k=st.kw||'amber';root.dataset.kw=k;
    dots.querySelector('.kwbtn').className='kwbtn kw-'+k;
    dots.querySelectorAll('.kwopt[data-k]').forEach(b=>b.classList.toggle('on',b.dataset.k===k));
    const d=st.kwd||'dense';root.dataset.kwd=d;const t=dots.querySelector('.kwdbtn');
    if(t){t.setAttribute('aria-pressed',String(d==='dense'));t.classList.toggle('on',d==='dense')}}
  dots.querySelectorAll('.dot[data-c]').forEach(b=>b.setAttribute('aria-pressed',String(!st.off.includes(b.dataset.c))));
  root.classList.toggle('ink-on',st.ink);box.querySelector('.inkbtn').classList.toggle('on',st.ink);
  root.style.setProperty('--ink-w',st.iw+'px');root.style.setProperty('--ink-h',st.ih+'px');
  save(st);curGraph&&setTimeout(()=>curGraph.draw(),0);
}
box.querySelector('.inkbtn').onclick=()=>{st.ink=!st.ink;apply()};
const grip=zone.querySelector('.grip');
grip.addEventListener('pointerdown',e=>{e.preventDefault();try{grip.setPointerCapture(e.pointerId)}catch(x){}root.classList.add('ink-drag');
  const mv=ev=>{st.cal=true;st.iw=Math.round(Math.min(innerWidth-360,Math.max(300,innerWidth-16-ev.clientX)));st.ih=Math.round(Math.min(innerHeight-200,Math.max(120,innerHeight-8-ev.clientY)));apply()};
  const up=()=>{grip.removeEventListener('pointermove',mv);grip.removeEventListener('pointerup',up);root.classList.remove('ink-drag')};
  grip.addEventListener('pointermove',mv);grip.addEventListener('pointerup',up)});
grip.ondblclick=()=>{delete st.cal;st.iw=DEF[0];st.ih=DEF[1];apply()};
apply();spy();
})();
