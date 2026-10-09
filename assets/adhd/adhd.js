/* ADHD 版阅读地图：统计各类荧光标注，按类开关，点卡片跳到原文。 */
(()=>{
const CATS=[
 ['thesis','结论','定理、结论与总结句','var(--hl-thesis-ink)','var(--hl-thesis)'],
 ['claim','方法','思路、步骤与关键一步','var(--hl-claim-ink)','var(--hl-claim)'],
 ['evidence','例子','例题题目与举例','var(--hl-evidence-ink)','var(--hl-evidence)'],
 ['counter','易错','提醒、反例与限制条件','var(--hl-counter-ink)','var(--hl-counter)'],
 ['term','概念','定义与关键术语','var(--hl-term-ink)','var(--hl-term)']];
const KEY='adhd-map:'+location.pathname;
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}};
const save=s=>{try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}};
const st=Object.assign({off:[],closed:false,only:null},load());
const root=document.documentElement;
const items=[...document.querySelectorAll('main [data-cat]')];
const count=c=>items.filter(x=>x.dataset.cat===c).length;
const section=el=>{let h=null;for(const x of document.querySelectorAll('main h2,main h3')){if(x.compareDocumentPosition(el)&Node.DOCUMENT_POSITION_FOLLOWING)h=x;else break}return h?h.textContent.trim():''};
const txt=el=>{const c=el.cloneNode(true);c.querySelectorAll('math').forEach(m=>{const a=m.querySelector('annotation');m.replaceWith(a?a.textContent:'…')});return c.textContent.replace(/\s+/g,' ').trim()};

const box=document.createElement('div');box.id='rmap';box.setAttribute('role','complementary');box.setAttribute('aria-label','阅读地图');
box.innerHTML=`<header><span>阅读地图</span><button title="收起" aria-label="收起阅读地图">×</button></header>
<div class="sum">${items.length} 处标注</div><div class="legend-list"></div><div class="cards"></div>
<footer>点颜色开关该类；双击只看该类。点卡片跳到原文。</footer>`;
const open=document.createElement('button');open.id='rmap-open';open.textContent='阅读地图';
document.body.append(box,open);
const list=box.querySelector('.legend-list'),cards=box.querySelector('.cards');
for(const [c,name,desc,ink,bg] of CATS){
  const b=document.createElement('button');b.className='cat';b.dataset.c=c;
  b.innerHTML=`<i class="dot" style="background:${ink}"></i><b>${name}</b><span class="desc">${desc}</span><em>${count(c)}</em>`;
  b.onclick=()=>{const i=st.off.indexOf(c);i<0?st.off.push(c):st.off.splice(i,1);st.only=null;apply()};
  b.ondblclick=()=>{st.only=st.only===c?null:c;st.off=st.only?CATS.map(x=>x[0]).filter(x=>x!==c):[];apply()};
  list.append(b);
}
let built=false;
function buildCards(){
  const frag=document.createDocumentFragment();
  for(const el of items){
    const meta=CATS.find(x=>x[0]===el.dataset.cat);if(!meta)continue;
    const t=txt(el);const card=document.createElement('button');card.className='card';card.dataset.c=meta[0];
    card.innerHTML=`<span class="tag" style="color:${meta[3]};background:${meta[4]}">${meta[1]}</span><br>`;
    card.append(document.createTextNode(t.length>110?t.slice(0,110)+'…':t));
    const w=document.createElement('span');w.className='where';w.textContent=section(el);card.append(w);
    card.onclick=()=>{const d=el.closest('details');if(d)d.open=true;el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1600)};
    frag.append(card);
  }
  cards.append(frag);built=true;
}
function apply(){
  for(const [c] of CATS)root.classList.toggle('off-'+c,st.off.includes(c));
  list.querySelectorAll('.cat').forEach(b=>{b.setAttribute('aria-pressed',String(!st.off.includes(b.dataset.c)));b.classList.toggle('only',st.only===b.dataset.c)});
  cards.querySelectorAll('.card').forEach(k=>k.hidden=st.off.includes(k.dataset.c));
  root.classList.toggle('rmap-closed',!!st.closed);save(st);
}
box.querySelector('header button').onclick=()=>{st.closed=true;apply()};
open.onclick=()=>{st.closed=false;apply()};
// 术语较多时卡片列表很长，空闲时再生成，避免拖慢首屏
(window.requestIdleCallback||setTimeout)(()=>{buildCards();apply()});
apply();
})();
