/* ADHD 大纲版：右侧面板实时显示当前章的概念大纲（小节 → 定义/定理/结论/易错/例题/关键词），
   并给右下角的触控板手写小窗让出位置。荧光标注样式沿用 adhd.css。 */
(()=>{
const KEY='adhd-outline:'+location.pathname;
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}};
const save=s=>{try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}};
const st=Object.assign({off:[],closed:false,ink:'m',ex:true},load());
const INK={off:0,s:190,m:270,l:370};
const INK_NAME={off:'关',s:'小',m:'中',l:'大'};
const root=document.documentElement,main=document.querySelector('main');
const KIND={definition:['定义','term'],theorem:['定理','thesis'],result:['结论','thesis'],warning:['易错','counter'],example:['例题','evidence'],question:['思考','claim']};
const CATS=[['thesis','结论'],['claim','方法'],['evidence','例子'],['counter','易错'],['term','概念']];
const txt=el=>{const c=el.cloneNode(true);c.querySelectorAll('math').forEach(m=>{const a=m.querySelector('annotation');m.replaceWith(a?a.textContent:'…')});return c.textContent.replace(/\s+/g,' ').trim()};

/* 1. 按文档顺序把块和加粗术语归到最近的标题下 */
const secs=[];let cur=null;
for(const el of main.querySelectorAll('h2,h3,div.block,strong.kt,mark.hl-thesis,mark.hl-claim,mark.hl-counter,.math.display')){
  if(el.tagName==='H2'||el.tagName==='H3'){
    if(!el.id)continue;
    cur={h:el,lv:el.tagName==='H2'?2:3,title:txt(el),blocks:[],terms:[],pts:[],eqs:[]};secs.push(cur);continue;
  }
  if(!cur)continue;
  // 不在定理、结论块里的结论句，作为本节“要点”
  if(el.tagName==='MARK'){if(!el.closest('div.block')&&!el.closest('details'))cur.pts.push({t:txt(el),el,c:el.dataset.cat});continue}
  // 带框的最终结果公式
  if(el.classList.contains('display')){const a=el.querySelector('annotation');if(a&&/\\boxed/.test(a.textContent)&&!el.closest('details'))cur.eqs.push(el);continue}
  if(el.tagName==='STRONG'){const t=txt(el);if(t&&!cur.terms.some(x=>x.t===t))cur.terms.push({t,el});continue}
  const kind=[...el.classList].find(c=>KIND[c]);if(!kind)continue;
  const tt=el.querySelector('.block-title');if(!tt)continue;
  // “定义 3 · n 次方根” → 名称“n 次方根”
  let name=txt(tt).replace(/^[^·]*·\s*/,'');if(!name)name=txt(tt);
  cur.blocks.push({kind,name,el});
}
// 章：h2 及其下的 h3
const chaps=[];
for(const s of secs){if(s.lv===2||!chaps.length)chaps.push({head:s,subs:[]});else chaps[chaps.length-1].subs.push(s)}
const chapOf=new Map();chaps.forEach((c,i)=>{chapOf.set(c.head,i);c.subs.forEach(s=>chapOf.set(s,i))});

/* 2. 面板 */
const box=document.createElement('div');box.id='olmap';box.setAttribute('role','complementary');box.setAttribute('aria-label','本章概念大纲');
box.innerHTML=`<header><span>概念大纲</span>
<span class="ink" title="给右下角的手写小窗留出的高度"><i>手写区</i>${Object.keys(INK).map(k=>`<button data-ink="${k}">${INK_NAME[k]}</button>`).join('')}</span>
<button class="x" title="收起" aria-label="收起大纲">×</button></header>
<nav class="chap"><button class="prev" aria-label="上一章">‹</button><button class="ct"></button><button class="next" aria-label="下一章">›</button></nav>
<div class="tree"></div>
<footer><span class="dots"></span><label><input type="checkbox" class="exs"> 例题</label></footer>`;
const open=document.createElement('button');open.id='olmap-open';open.textContent='概念大纲';
const zone=document.createElement('div');zone.id='ink-zone';zone.textContent='手写窗口区';
document.body.append(box,open,zone);
const tree=box.querySelector('.tree'),ct=box.querySelector('.ct');
const dots=box.querySelector('.dots');
for(const [c,n] of CATS){const b=document.createElement('button');b.className='dot hl-'+c;b.dataset.c=c;b.title=n+'：点击开关该类荧光';b.textContent=n;
  b.onclick=()=>{const i=st.off.indexOf(c);i<0?st.off.push(c):st.off.splice(i,1);apply()};dots.append(b)}

const jump=el=>{const d=el.closest('details');if(d)d.open=true;el.scrollIntoView({behavior:'smooth',block:el.tagName[0]==='H'?'start':'center'});
  el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1600)};
const node=(cls,label,text,el)=>{const b=document.createElement('button');b.className='n '+cls;
  if(label){const t=document.createElement('span');t.className='k';t.textContent=label;b.append(t)}
  b.append(document.createTextNode(text));b.onclick=e=>{e.stopPropagation();jump(el)};return b};

function concepts(s){
  const wrap=document.createElement('div');wrap.className='kids';
  for(const b of s.blocks){const [lab,cat]=KIND[b.kind];
    const n=node('c-'+cat+(b.kind==='example'||b.kind==='question'?' ex':''),lab,b.name,b.el);wrap.append(n)}
  for(const e of s.eqs.slice(0,2)){const b=node('c-thesis eq','结果','',e);const m=e.querySelector('math').cloneNode(true);m.setAttribute('display','inline');b.append(m);wrap.append(b)}
  // 没有定义、定理时，用结论句补位；再没有就用方法、易错句
  if(!s.blocks.some(b=>KIND[b.kind][1]!=='evidence'&&b.kind!=='warning')){
    const lab={thesis:'要点',claim:'方法',counter:'易错'};
    let ps=s.pts.filter(p=>p.c==='thesis').slice(0,3);
    if(!ps.length&&!s.eqs.length)ps=s.pts.slice(0,2);
    for(const p of ps)wrap.append(node('c-'+p.c+' pt',lab[p.c],p.t.length>46?p.t.slice(0,46)+'…':p.t,p.el));
  }
  const used=new Set(s.blocks.map(b=>b.name));
  const terms=s.terms.filter(t=>!used.has(t.t)).slice(0,12);
  if(terms.length){const r=document.createElement('div');r.className='terms';
    for(const t of terms){const b=document.createElement('button');b.className='chip';b.textContent=t.t;b.onclick=e=>{e.stopPropagation();jump(t.el)};r.append(b)}
    wrap.append(r)}
  return wrap;
}
// 收起时的一行摘要：只列定义与定理的名字
const brief=s=>s.blocks.filter(b=>b.kind==='definition'||b.kind==='theorem').map(b=>b.name).join('、');

let shown=-1,curSec=null;
function renderChap(i){
  shown=i;const c=chaps[i];tree.textContent='';
  ct.textContent=c.head.title;ct.onclick=()=>jump(c.head.h);
  box.querySelector('.prev').disabled=i===0;box.querySelector('.next').disabled=i===chaps.length-1;
  const list=[c.head,...c.subs];
  for(const s of list){
    const li=document.createElement('div');li.className='sec'+(s===c.head?' intro':'');li.sec=s;
    if(s===c.head&&!s.blocks.length&&!s.terms.length&&!s.pts.length&&!s.eqs.length)continue;
    const h=document.createElement('button');h.className='st';h.textContent=s===c.head?'本章导入':s.title;h.onclick=()=>jump(s.h);li.append(h);
    const b=brief(s);if(b){const p=document.createElement('div');p.className='brief';p.textContent=b;li.append(p)}
    li.append(concepts(s));tree.append(li);
  }
  mark(curSec);
}
function mark(s){
  tree.querySelectorAll('.sec').forEach(li=>li.classList.toggle('cur',li.sec===s));
  const c=tree.querySelector('.sec.cur');
  if(c){const r=c.getBoundingClientRect(),R=tree.getBoundingClientRect();if(r.top<R.top||r.top>R.bottom-60)tree.scrollTop+=r.top-R.top-8}
}
box.querySelector('.prev').onclick=()=>{renderChap(shown-1);jump(chaps[shown].head.h)};
box.querySelector('.next').onclick=()=>{renderChap(shown+1);jump(chaps[shown].head.h)};

/* 3. 跟随阅读位置 */
function spy(){
  let s=secs[0];
  for(const x of secs){if(x.h.getBoundingClientRect().top<150)s=x;else break}
  if(!s)return;
  const i=chapOf.get(s);
  if(s!==curSec||i!==shown){curSec=s;i!==shown?renderChap(i):mark(s)}
}
let tick=false;addEventListener('scroll',()=>{if(!tick){tick=true;requestAnimationFrame(()=>{tick=false;spy()})}},{passive:true});

/* 4. 状态 */
function apply(){
  for(const [c] of CATS)root.classList.toggle('off-'+c,st.off.includes(c));
  dots.querySelectorAll('.dot').forEach(b=>b.setAttribute('aria-pressed',String(!st.off.includes(b.dataset.c))));
  root.style.setProperty('--ink-h',INK[st.ink]+'px');
  root.classList.toggle('ink-on',st.ink!=='off');
  box.querySelectorAll('[data-ink]').forEach(b=>b.classList.toggle('on',b.dataset.ink===st.ink));
  root.classList.toggle('ol-closed',!!st.closed);
  root.classList.toggle('ol-noex',!st.ex);box.querySelector('.exs').checked=st.ex;
  save(st);
}
box.querySelectorAll('[data-ink]').forEach(b=>b.onclick=()=>{st.ink=b.dataset.ink;apply()});
box.querySelector('.exs').onchange=e=>{st.ex=e.target.checked;apply()};
box.querySelector('.x').onclick=()=>{st.closed=true;apply()};
open.onclick=()=>{st.closed=false;apply()};
apply();spy();
})();
