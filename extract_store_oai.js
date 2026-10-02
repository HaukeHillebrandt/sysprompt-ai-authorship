const sleep=ms=>new Promise(r=>setTimeout(r,ms));
for(let k=0;k<30 && !document.body.innerText.includes('words scanned');k++) await sleep(500);
const D=document; const t=D.body.innerText; const i=t.indexOf('words scanned');
const ov=t.slice(Math.max(0,i-40),i+200).replace(/\n/g,'|');
const id=(location.search.match(/history=([\w-]+)/)||[])[1];
const ids=JSON.parse(localStorage.getItem('oai_ids')); const nn=(Object.entries(ids).find(([k,v])=>v.startsWith(id))||['OAI_??'])[0].slice(4,6);
const out={nn, ov:(ov.match(/([\d,]+ words scanned).*?(\d+\|%\|of this text is[^|]*)/)||[]).slice(1).join(' ')};
const b=[...D.querySelectorAll('button,[role=tab]')].find(b=>b.textContent.trim()==='Details');
for (const ev of ['pointerdown','mousedown','pointerup','mouseup','click']) b.dispatchEvent(new (ev.startsWith('pointer')?PointerEvent:MouseEvent)(ev,{bubbles:true,button:0}));
await sleep(1200);
let panel; const segs=[]; let pages=0;
for(let p=0;p<120;p++){
  panel=[...D.querySelectorAll('[role=tabpanel]')].find(x=>x.textContent.includes('All Segments'));
  panel.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach(h=>{const s=h.textContent.trim(); if(/words/.test(s)) segs.push(s);});
  const pg=[...panel.querySelectorAll('*')].map(e=>e.children.length===0?e.textContent.trim():'').find(s=>/^\d+ \/ \d+$/.test(s));
  pages=pg; if(!pg) break; const [a,c]=pg.split(' / ').map(Number); if(a>=c) break;
  const btns=[...panel.querySelectorAll('button')]; btns[btns.length-1].click(); await sleep(800);
}
const clean=s=>s.replace(/[^A-Za-z0-9 ,.:'()\/-]/g,' ').replace(/\s+/g,' ').trim();
out.segs=segs.map(s=>{const m=s.match(/^(Human Written|AI-assisted|AI Assisted|Lightly AI-assisted|Moderately AI-assisted|Heavily AI-assisted|Assisted|AI|Mixed)\s*(high|medium|low)\s*([\d,]+) words\s*([\s\S]{0,45})/i); return m?`${nn}|${m[1]==='AI'?'A':m[1]==='Human Written'?'H':clean(m[1])}${m[2][0]}|${m[3].replace(/,/g,'')}|${clean(m[4]).slice(0,30)}`:`${nn}|X|0|${clean(s).slice(0,30)}`;});
localStorage.setItem('oaiseg_'+nn, JSON.stringify(out));
const aw=out.segs.filter(s=>s.split('|')[1].startsWith('A')).reduce((a,s)=>a+ +s.split('|')[2],0), tw=out.segs.reduce((a,s)=>a+ +s.split('|')[2],0);
`${nn} ${out.ov} | segs=${out.segs.length} pages=${pages} | AI words ${aw}/${tw}`
