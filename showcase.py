"""Animated watch showcase (carousel) rendered inside Streamlit as a self-contained HTML component."""
import json
import watch_art as W

TEMPLATE = r"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box} body{margin:0;font-family:'Inter',Arial,sans-serif;background:transparent}
.stage{position:relative;overflow:hidden;border-radius:26px;padding:18px 20px 14px;color:#fff;
 background:radial-gradient(900px 420px at 50% 28%,#2A4FB8 0%,#142A78 45%,#08174D 100%);
 border:1px solid rgba(201,162,75,.55);box-shadow:0 18px 50px rgba(10,31,92,.28), inset 0 0 0 5px rgba(255,255,255,.04)}
.stage:before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;opacity:.5;
 background:repeating-linear-gradient(45deg,rgba(255,255,255,.025) 0 2px,transparent 2px 14px)}
.top{display:flex;justify-content:space-between;align-items:center;position:relative;z-index:2}
.crest{font-family:'Playfair Display',Georgia,serif;letter-spacing:.22em;font-size:12px;color:#E8D49A;font-weight:700}
.auto{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.25);color:#fff;border-radius:20px;
 padding:5px 13px;font-size:11px;cursor:pointer;letter-spacing:.06em}
.auto:hover{background:rgba(255,255,255,.2)}
.body{position:relative;z-index:2;text-align:center;animation-duration:.55s;animation-fill-mode:both}
.body.r{animation-name:inR} .body.l{animation-name:inL}
@keyframes inR{from{opacity:0;transform:translateX(70px)}to{opacity:1;transform:none}}
@keyframes inL{from{opacity:0;transform:translateX(-70px)}to{opacity:1;transform:none}}
.watchwrap{position:relative;height:__WH__px;margin:6px auto 0;width:min(100%,520px)}
.glow{position:absolute;left:50%;top:50%;width:300px;height:300px;transform:translate(-50%,-50%);border-radius:50%;
 background:radial-gradient(circle,rgba(255,255,255,.30),rgba(255,255,255,0) 68%)}
.watch{position:absolute;top:0;left:0;right:0;bottom:0;margin:0 auto;height:100%;width:__WW__px;animation:float 5s ease-in-out infinite;
 filter:drop-shadow(0 22px 20px rgba(0,0,0,.45))}
.watch img{width:100%;height:100%;object-fit:contain}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
@keyframes sweep{to{transform:rotate(360deg)}} .sweep{animation:sweep 60s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}} .gear{animation:spin 9s linear infinite}
.nav{position:absolute;top:__NAVTOP__px;z-index:5;width:50px;height:50px;border-radius:50%;cursor:pointer;color:#fff;font-size:26px;
 background:rgba(255,255,255,.12);border:1px solid rgba(232,212,154,.7);transition:.2s;line-height:44px;padding:0}
.nav:hover{background:#fff;color:#0A1F5C;transform:scale(1.08)} .prev{left:26px}.next{right:26px}
.rank{display:inline-block;font-size:11px;letter-spacing:.16em;color:#0A1F5C;background:linear-gradient(90deg,#F6E7B4,#C9A24B);
 padding:4px 14px;border-radius:20px;font-weight:700;margin-top:8px}
h2{font-family:'Playfair Display',Georgia,serif;font-size:30px;margin:8px 0 0;letter-spacing:.02em;color:#fff}
.tag{font-size:12px;letter-spacing:.2em;color:#B9C8F2;text-transform:uppercase;margin-top:2px}
.line{width:90px;height:2px;margin:10px auto 6px;background:linear-gradient(90deg,transparent,#C9A24B,transparent)}
.big{font-family:'Playfair Display',Georgia,serif;font-size:58px;font-weight:800;line-height:1.05;color:#fff;
 text-shadow:0 4px 24px rgba(0,0,0,.35)}
.bl{font-size:12px;letter-spacing:.24em;color:#E8D49A;text-transform:uppercase;margin-top:2px}
.chips{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:14px 0 4px}
.chip{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.2);border-radius:14px;padding:8px 16px;min-width:108px;
 backdrop-filter:blur(4px)}
.chip b{display:block;font-size:17px;color:#fff} .chip span{font-size:10px;letter-spacing:.14em;color:#B9C8F2;text-transform:uppercase}
.thumbs{position:relative;z-index:2;display:flex;gap:10px;overflow-x:auto;padding:12px 4px 6px;margin-top:10px;
 border-top:1px solid rgba(255,255,255,.14);scrollbar-width:thin;scrollbar-color:#C9A24B transparent}
.th{flex:0 0 auto;width:74px;text-align:center;cursor:pointer;opacity:.55;transition:.2s;border-radius:14px;padding:6px 2px 4px;
 border:1px solid transparent}
.th:hover{opacity:1} .th.on{opacity:1;background:rgba(255,255,255,.1);border-color:#C9A24B}
.th .ti{height:84px} .th small{display:block;font-size:9px;color:#DDE6FF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar{position:absolute;left:0;bottom:0;height:3px;background:linear-gradient(90deg,#C9A24B,#F6E7B4);width:0;z-index:3}
@media(max-width:620px){.big{font-size:42px}h2{font-size:23px}.nav{width:40px;height:40px;font-size:20px;line-height:34px}.prev{left:8px}.next{right:8px}}
</style>
<div class="stage" id="stage" tabindex="0">
 <div class="top"><div class="crest">♛ &nbsp;__TITLE__</div><button class="auto" id="auto">❚❚ AUTO</button></div>
 <button class="nav prev" id="prev">‹</button><button class="nav next" id="next">›</button>
 <div class="body r" id="body">
  <div class="watchwrap"><div class="glow"></div><div class="watch" id="watch"></div></div>
  <div><span class="rank" id="rank"></span></div>
  <h2 id="name"></h2><div class="tag" id="tag"></div><div class="line"></div>
  <div class="big" id="count">0</div><div class="bl" id="bl"></div>
  <div class="chips" id="chips"></div>
 </div>
 <div class="thumbs" id="thumbs"></div>
 <div class="bar" id="bar"></div>
</div>
<script>
const D=__DATA__, N=D.length, INTERVAL=6000;
let i=0, auto=true, t0=Date.now(), anim=null;
const $=id=>document.getElementById(id);
const fmt=v=>Math.round(v).toLocaleString('en-IN');
function countUp(to){cancelAnimationFrame(anim);const s=performance.now();
 (function f(n){const k=Math.min(1,(n-s)/1100),e=1-Math.pow(1-k,3);$('count').textContent=fmt(to*e);if(k<1)anim=requestAnimationFrame(f)})(s)}
function render(dir){
 const m=D[i], b=$('body'); b.className='body '+(dir<0?'l':'r'); void b.offsetWidth;
 $('watch').innerHTML=m.img?'<img src="'+m.img+'">':m.svg;
 $('rank').textContent=m.badge; $('name').textContent=m.name; $('tag').textContent=m.tag;
 $('bl').textContent=m.label; countUp(m.value);
 $('chips').innerHTML=m.stats.map(s=>'<div class="chip"><b>'+s[1]+'</b><span>'+s[0]+'</span></div>').join('');
 document.querySelectorAll('.th').forEach((e,k)=>e.classList.toggle('on',k===i));
 const on=document.querySelectorAll('.th')[i], th=$('thumbs');
 th.scrollTo({left:on.offsetLeft-th.clientWidth/2+on.clientWidth/2,behavior:'smooth'}); t0=Date.now();
}
function go(d){i=(i+d+N)%N;render(d)}
function jump(k){const d=k>=i?1:-1;i=k;render(d)}
$('thumbs').innerHTML=D.map((m,k)=>'<div class="th" onclick="jump('+k+')"><div class="ti">'+(m.timg?'<img src="'+m.timg+'" style="width:100%;height:100%;object-fit:contain">':m.tsvg)+'</div><small>'+m.short+'</small></div>').join('');
$('prev').onclick=()=>go(-1); $('next').onclick=()=>go(1);
$('auto').onclick=()=>{auto=!auto;$('auto').textContent=auto?'❚❚ AUTO':'▶ AUTO';t0=Date.now()};
$('stage').addEventListener('keydown',e=>{if(e.key==='ArrowRight')go(1);if(e.key==='ArrowLeft')go(-1)});
let hover=false;$('stage').onmouseenter=()=>hover=true;$('stage').onmouseleave=()=>{hover=false;t0=Date.now()};
setInterval(()=>{const p=Math.min(1,(Date.now()-t0)/INTERVAL);$('bar').style.width=(auto?p*100:0)+'%';
 if(auto&&!hover&&p>=1)go(1)},100);
render(1);
</script>
"""

def build(items, title="MODEL SHOWCASE", height=700):
    """items: list of dicts with name, collection, strap, value, label, badge, stats=[(label, text)], short"""
    data = []
    for k, it in enumerate(items):
        img = W.find_image(it["name"], it["collection"])
        data.append(dict(name=it["name"], tag=f'{it["collection"]} · {it["strap"]} strap', label=it["label"],
                         value=float(it["value"]), badge=it["badge"], stats=it["stats"], short=it["name"],
                         img=img, timg=img,
                         svg=W.watch_svg(it["collection"], it["strap"], f"m{k}", True),
                         tsvg=W.watch_svg(it["collection"], it["strap"], f"t{k}", False)))
    wh = 300
    html = (TEMPLATE.replace("__DATA__", json.dumps(data).replace("</", "<\\/")).replace("__TITLE__", title)
            .replace("__WH__", str(wh)).replace("__WW__", str(int(wh * 0.65))).replace("__NAVTOP__", str(150)))
    return html, height
