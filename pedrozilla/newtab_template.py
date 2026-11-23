"""Plantilla HTML de la nueva pestaña (diseño adjuntado por el usuario)."""

TEMPLATE = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nueva pestaña · __BRAND__</title>
<style>
:root{
  --ink:#202321;--muted:#727a75;--glass:rgba(250,251,247,.78);
  --glass-border:rgba(255,255,255,.72);--accent:__ACCENT__;
  --shadow:0 16px 44px rgba(25,37,30,.13),0 2px 8px rgba(25,37,30,.06);
  --radius:17px;
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink)}
body{min-height:100vh;overflow-x:hidden;background:#d9ded4}
button,input{font:inherit}
button{cursor:pointer}
.wallpaper{position:fixed;inset:0;z-index:-2;background:
linear-gradient(180deg,rgba(248,247,239,.55) 0%,rgba(241,241,232,.22) 38%,rgba(18,35,30,.12) 100%),
url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 1000'%3E%3Cdefs%3E%3ClinearGradient id='sky' x2='0' y2='1'%3E%3Cstop stop-color='%23e9e9df'/%3E%3Cstop offset='.48' stop-color='%23c4cbbd'/%3E%3Cstop offset='1' stop-color='%233b5146'/%3E%3C/linearGradient%3E%3ClinearGradient id='fog' x2='0' y2='1'%3E%3Cstop stop-color='%23fff' stop-opacity='.52'/%3E%3Cstop offset='1' stop-color='%23fff' stop-opacity='0'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1600' height='1000' fill='url(%23sky)'/%3E%3Cpath d='M0 430 Q240 300 440 430 T900 410 T1600 390 V1000 H0Z' fill='%2396a493' opacity='.5'/%3E%3Cpath d='M0 560 Q250 390 520 560 T1050 520 T1600 540 V1000 H0Z' fill='%236c8272' opacity='.65'/%3E%3Cg fill='%232f493d'%3E%3Cpath d='M-40 1000 L80 300 200 1000Z M100 1000 L230 180 370 1000Z M280 1000 L390 330 510 1000Z M450 1000 L580 120 720 1000Z M660 1000 L790 280 920 1000Z M850 1000 L1000 170 1150 1000Z M1080 1000 L1210 260 1350 1000Z M1280 1000 L1430 110 1580 1000Z M1450 1000 L1570 330 1690 1000Z'/%3E%3C/g%3E%3Cg fill='%234b6654' opacity='.9'%3E%3Cpath d='M-70 1000 L40 470 150 1000Z M180 1000 L300 390 420 1000Z M390 1000 L500 480 610 1000Z M600 1000 L730 370 860 1000Z M830 1000 L940 470 1050 1000Z M1040 1000 L1160 390 1280 1000Z M1260 1000 L1380 440 1500 1000Z M1460 1000 L1570 480 1680 1000Z'/%3E%3C/g%3E%3Cg stroke='%232b4036' stroke-width='9' opacity='.75'%3E%3Cpath d='M120 1000V390 M270 1000V270 M460 1000V430 M640 1000V240 M880 1000V380 M1090 1000V280 M1320 1000V360 M1510 1000V260'/%3E%3C/g%3E%3Crect width='1600' height='620' fill='url(%23fog)'/%3E%3C/svg%3E") center/cover no-repeat;
transform:scale(1.02)}
.wallpaper:after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(248,247,242,.15),transparent 45%,rgba(12,25,20,.16))}
.topbar{width:min(960px,calc(100% - 36px));height:54px;margin:13px auto 0;display:flex;align-items:center;gap:10px;position:relative}
.pill,.searchbox,.toolbtn{border:1px solid rgba(255,255,255,.65);background:rgba(255,255,255,.67);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);box-shadow:0 3px 14px rgba(25,35,28,.045)}
.pill{height:38px;border-radius:12px;padding:0 13px;display:flex;align-items:center;gap:8px;font-size:13px;font-weight:650;white-space:nowrap}
.work-menu{position:relative}
.work-options{display:none;position:absolute;top:45px;left:0;min-width:180px;padding:7px;background:#fff;border:1px solid #e9ece7;border-radius:12px;box-shadow:var(--shadow);z-index:5}
.work-options.open{display:block}
.work-options button{display:block;width:100%;border:0;background:transparent;text-align:left;padding:9px 10px;border-radius:8px;color:#39413b;font-size:13px}
.work-options button:hover{background:#f0f2ed}
.searchbox{height:38px;border-radius:12px;display:flex;align-items:center;gap:9px;padding:0 13px;flex:1;min-width:80px}
.searchbox span{color:#7c847e;font-size:16px}
.searchbox input{border:0;outline:0;background:transparent;width:100%;font-size:13px;color:#29312b}
.searchbox input::placeholder{color:#858d87}
.tools{display:flex;gap:4px;align-items:center}
.toolbtn{width:34px;height:34px;border:0;border-radius:10px;color:#59625b;background:rgba(255,255,255,.36);font-size:16px}
.toolbtn:hover,.pill:hover{background:rgba(255,255,255,.88)}
.avatar{width:34px;height:34px;border-radius:50%;border:2px solid rgba(255,255,255,.8);background:linear-gradient(135deg,#d7a66c,#7b8b62 55%,#455c50);display:grid;place-items:center;color:white;font-weight:700;font-size:12px;margin-left:4px}
main{width:min(960px,calc(100% - 36px));margin:25px auto 60px}
.hero{text-align:center;padding:7px 0 28px}
.clock{font-size:clamp(48px,6vw,58px);font-weight:650;letter-spacing:-3px;line-height:1.12;color:#171b18;text-shadow:0 2px 15px rgba(255,255,255,.25)}
.date-line{margin-top:8px;font-size:12px;color:#59635c;font-weight:500}
.greeting{margin-top:10px;font-size:13px;color:#4c554e}
.weather{display:inline-flex;gap:6px;align-items:center;margin-left:8px;color:#66716a}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;align-items:start}
.card{background:var(--glass);border:1px solid var(--glass-border);border-radius:var(--radius);box-shadow:var(--shadow);backdrop-filter:blur(19px);-webkit-backdrop-filter:blur(19px);padding:14px 14px 12px;min-height:190px;overflow:hidden}
.card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;color:#555f58}
.card-title{display:flex;align-items:center;gap:7px;font-size:10px;letter-spacing:.045em;font-weight:750}
.count{font-size:10px;color:#89918a}
.item-list{display:flex;flex-direction:column;gap:3px}
.note-item,.reminder-item,.link-item{display:flex;align-items:center;gap:8px;min-height:29px;padding:4px 5px;border-radius:8px;font-size:12px;color:#303832}
.note-item:hover,.reminder-item:hover,.link-item:hover{background:rgba(255,255,255,.55)}
.note-item .txt,.reminder-item .txt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.note-item.done .txt,.reminder-item.done .txt{text-decoration:line-through;color:#8b938d}
.check{width:13px;height:13px;border:1px solid #cbd2ca;border-radius:4px;flex:none;display:grid;place-items:center;color:white;font-size:9px;background:rgba(255,255,255,.45);padding:0}
.done .check{background:#38b879;border-color:#38b879}
.remove{opacity:0;border:0;background:transparent;color:#879087;padding:2px 4px;font-size:14px}
.note-item:hover .remove,.reminder-item:hover .remove,.link-item:hover .remove{opacity:1}
.add-row{display:flex;align-items:center;gap:6px;border:0;background:transparent;color:#929b94;font-size:11px;padding:9px 4px 2px;width:100%;text-align:left}
.add-row:hover{color:#4c6656}
.link-item{min-height:39px;text-decoration:none;color:#2d342f}
.site-icon{width:19px;height:19px;border-radius:6px;background:rgba(255,255,255,.82);display:grid;place-items:center;font-size:11px;font-weight:800;flex:none;color:#536b5c}
.link-meta{display:flex;flex-direction:column;min-width:0;flex:1;gap:1px}
.link-name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.link-url{font-size:10px;color:#879087;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.section-add{grid-column:1/-1;text-align:left;margin-top:4px}
.section-add button{border:0;background:rgba(255,255,255,.3);color:rgba(255,255,255,.9);padding:8px 12px;border-radius:9px;font-size:12px;text-shadow:0 1px 5px rgba(0,0,0,.3)}
.empty{font-size:11px;color:#929a93;padding:8px 4px}
.modal-backdrop{position:fixed;inset:0;background:rgba(20,28,23,.3);backdrop-filter:blur(5px);display:none;align-items:center;justify-content:center;padding:20px;z-index:20}
.modal-backdrop.open{display:flex}
.modal{width:min(390px,100%);background:#fbfcf9;border:1px solid white;border-radius:18px;padding:20px;box-shadow:0 25px 80px rgba(0,0,0,.2)}
.modal h2{font-size:17px;margin:0 0 14px}
.modal label{display:block;font-size:11px;color:#69736b;margin:10px 0 5px}
.modal input{width:100%;padding:10px 11px;border:1px solid #e1e6df;border-radius:9px;outline:0;background:white;font-size:13px}
.modal input:focus{border-color:#a6b8a9;box-shadow:0 0 0 3px rgba(116,151,123,.13)}
.modal-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:17px}
.modal-actions button{border:0;border-radius:9px;padding:9px 13px;font-size:12px}
.cancel{background:#edf0eb;color:#59635b}.save{background:__ACCENT__;color:white;font-weight:650}
.toast{position:fixed;bottom:22px;left:50%;transform:translate(-50%,15px);opacity:0;pointer-events:none;background:#202923;color:white;padding:10px 15px;border-radius:10px;font-size:12px;transition:.22s;z-index:30}
.toast.show{opacity:1;transform:translate(-50%,0)}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.tools .optional{display:none}}
@media(max-width:520px){.topbar{gap:6px}.pill{padding:0 9px}.tools{gap:0}.toolbtn{width:29px}.avatar{display:none}.grid{grid-template-columns:1fr}.hero{padding-top:25px}.card{min-height:unset}.section-add{grid-column:1}}
</style>
</head>
<body>
<div class="wallpaper"></div>
<header class="topbar">
  <div class="work-menu">
    <button class="pill" id="workBtn">🗂 <span id="workspaceName">__WORKSPACE__</span> <span style="font-size:10px">⌄</span></button>
    <div class="work-options" id="workOptions">
      <button data-work="Work">💼 Work</button><button data-work="Personal">🏡 Personal</button><button data-work="Study">📚 Study</button><button data-work="Create">＋ Nuevo espacio…</button>
    </div>
  </div>
  <div class="searchbox"><span>⌕</span><input id="search" placeholder="Buscar marcadores..." autocomplete="off"></div>
  <div class="tools">
    <button class="toolbtn optional" title="Deshacer" id="undoBtn">↶</button>
    <button class="toolbtn optional" title="Rehacer" id="redoBtn">↷</button>
    <button class="toolbtn" title="Historial" id="historyBtn">◷</button>
    <button class="toolbtn optional" title="Atajos" id="shortcutsBtn">⌘</button>
    <button class="toolbtn" title="Ajustes" id="settingsBtn">⚙</button>
  </div>
  <div class="avatar" title="PedroZilla">P</div>
</header>

<main>
  <section class="hero">
    <div class="clock" id="clock">09:41</div>
    <div class="date-line"><span id="date">Lunes, 23 de noviembre</span><span class="weather">☁ <span id="weatherText">Tu espacio personal</span></span></div>
    <div class="greeting" id="greeting">Buenos días.</div>
  </section>
  <section class="grid" id="grid">
    <article class="card" data-section="notes">
      <div class="card-head"><div class="card-title">♧ NOTAS</div><span class="count" id="notesCount">0</span></div>
      <div class="item-list" id="notesList"></div>
      <button class="add-row" data-add="note">＋ Añadir una nota</button>
    </article>
    <article class="card" data-section="reminders">
      <div class="card-head"><div class="card-title">♧ RECORDATORIOS</div><span class="count" id="remindersCount">0</span></div>
      <div class="item-list" id="remindersList"></div>
      <button class="add-row" data-add="reminder">＋ Añadir recordatorio</button>
    </article>
    <article class="card" data-section="build">
      <div class="card-head"><div class="card-title">◆ BUILD</div><span class="count" id="buildCount">0</span></div>
      <div class="item-list" id="buildList"></div>
      <button class="add-row" data-add="build">＋ Añadir enlace</button>
    </article>
    <article class="card" data-section="daily">
      <div class="card-head"><div class="card-title">✦ DAILY</div><span class="count" id="dailyCount">0</span></div>
      <div class="item-list" id="dailyList"></div>
      <button class="add-row" data-add="daily">＋ Añadir enlace</button>
    </article>
    <div class="section-add"><button id="newSection">＋ Nueva sección</button></div>
  </section>
</main>

<div class="modal-backdrop" id="modalBackdrop">
  <div class="modal" role="dialog" aria-modal="true">
    <h2 id="modalTitle">Añadir elemento</h2>
    <div id="modalFields"></div>
    <div class="modal-actions"><button class="cancel" id="cancelModal">Cancelar</button><button class="save" id="saveModal">Guardar</button></div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
__QWEBCHANNEL_JS__
window.pedrozilla = undefined;
if (typeof qt !== 'undefined' && qt.webChannelTransport) {
  new QWebChannel(qt.webChannelTransport, function(channel){
    window.pedrozilla = channel.objects.pedrozilla;
  });
}
</script>
<script>
/* Diseño de la nueva pestaña adjuntada, integrado con el puente de Pedrozilla. */
const $ = s => document.querySelector(s);
const PZ = __CONFIG_JSON__;
const defaults = {
  notes:[{text:"Lanzamiento: terminar la lista de comprobación",done:true},{text:"Objetivos semanales: revisar el progreso",done:false},{text:"Ideas de contenido: preparar borradores",done:false},{text:"Actualizar PedroZilla",done:false}],
  reminders:[{text:"Reunión de equipo",meta:"Cada lunes a las 10:00",done:false},{text:"Publicar entrada del blog",meta:"Esta semana",done:true},{text:"Revisar analíticas",meta:"Viernes",done:true},{text:"Preparar próxima versión",meta:"Mañana",done:false}],
  build:(PZ.shortcuts.length ? PZ.shortcuts : [{name:"GitHub",url:"https://github.com",icon:"●"},{name:"Linear",url:"https://linear.app",icon:"◆"},{name:"Vercel",url:"https://vercel.com",icon:"▲"},{name:"Loom",url:"https://loom.com",icon:"▣"},{name:"Figma",url:"https://figma.com",icon:"✿"}]),
  daily:(PZ.recent.length ? PZ.recent : [{name:"Gmail",url:"https://mail.google.com",icon:"M"},{name:"Calendar",url:"https://calendar.google.com",icon:"▦"},{name:"Slack",url:"https://slack.com",icon:"✣"},{name:"Notion",url:"https://notion.so",icon:"N"}]),
  sections:[]
};
let state = load();
let pending = null;
let undoStack = [], redoStack = [];
function load(){
  try{
    const saved = PZ.prefs && PZ.prefs["dashboard"];
    if (saved) return {...defaults,...(typeof saved === "string" ? JSON.parse(saved) : saved)};
  }catch(e){}
  return JSON.parse(JSON.stringify(defaults));
}
function persist(){
  if (!PZ.prefs || typeof PZ.prefs !== "object") PZ.prefs = {};
  PZ.prefs["dashboard"] = JSON.stringify(state);
  if (window.pedrozilla && window.pedrozilla.setNewTabPrefs) {
    try{ window.pedrozilla.setNewTabPrefs(JSON.stringify(PZ.prefs)); return; }catch(e){}
  }
  try{ localStorage.setItem("pedrozilla-newtab-prefs", JSON.stringify(PZ.prefs)); }catch(e){}
}
function snapshot(){undoStack.push(JSON.stringify(state));if(undoStack.length>30)undoStack.shift();redoStack=[]}
function toast(msg){const t=$("#toast");t.textContent=msg;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),1800)}
function escapeHTML(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function renderList(type){
 const list=$("#"+type+"List"),items=state[type]||[];
 $("#"+type+"Count").textContent=items.length;
 list.innerHTML=items.length?"":"<div class='empty'>Todavía no hay elementos</div>";
 items.forEach((item,i)=>{
  if(type==="notes"||type==="reminders"){
   const el=document.createElement("div");el.className=(type==="notes"?"note-item":"reminder-item")+(item.done?" done":"");
   el.innerHTML=`<button class="check" aria-label="Marcar">${item.done?"✓":""}</button><span class="txt" title="${escapeHTML(item.text)}">${escapeHTML(item.text)}</span>${type==="reminders"&&item.meta?`<small style="font-size:9px;color:#929a93">${escapeHTML(item.meta)}</small>`:""}<button class="remove" aria-label="Eliminar">×</button>`;
   el.querySelector(".check").onclick=()=>{snapshot();item.done=!item.done;persist();render()};
   el.querySelector(".remove").onclick=()=>{snapshot();state[type].splice(i,1);persist();render()};
   list.append(el);
  }else{
   const a=document.createElement("a");a.className="link-item";a.href=item.url;a.target="_blank";a.rel="noopener noreferrer";
   a.innerHTML=`<span class="site-icon">${escapeHTML(item.icon||item.name.slice(0,1).toUpperCase())}</span><span class="link-meta"><span class="link-name">${escapeHTML(item.name)}</span><span class="link-url">${escapeHTML(item.url.replace(/^https?:\/\//,""))}</span></span><button class="remove" aria-label="Eliminar">×</button>`;
   a.querySelector(".remove").onclick=e=>{e.preventDefault();e.stopPropagation();snapshot();state[type].splice(i,1);persist();render()};
   list.append(a);
  }
 });
}
function render(){
 ["notes","reminders","build","daily"].forEach(renderList);
 const grid=$("#grid");
 grid.querySelectorAll(".custom-card").forEach(e=>e.remove());
 (state.sections||[]).forEach((s,i)=>{
  const card=document.createElement("article");card.className="card custom-card";
  card.innerHTML=`<div class="card-head"><div class="card-title">${escapeHTML(s.icon||"✧")} ${escapeHTML(s.name.toUpperCase())}</div><button class="remove" style="opacity:1" aria-label="Eliminar sección">×</button></div><div class="item-list"></div><button class="add-row">＋ Añadir enlace</button>`;
  card.querySelector(".remove").onclick=()=>{snapshot();state.sections.splice(i,1);persist();render()};
  card.querySelector(".add-row").onclick=()=>openModal("link",`Enlace para ${s.name}`,item=>{snapshot();s.items=s.items||[];s.items.push(item);persist();render()});
  const list=card.querySelector(".item-list");
  (s.items||[]).forEach((it,j)=>{const a=document.createElement("a");a.className="link-item";a.href=it.url;a.target="_blank";a.rel="noopener noreferrer";a.innerHTML=`<span class="site-icon">${escapeHTML(it.icon||"↗")}</span><span class="link-meta"><span class="link-name">${escapeHTML(it.name)}</span><span class="link-url">${escapeHTML(it.url)}</span></span>`;list.append(a)});
  grid.insertBefore(card,grid.querySelector(".section-add"));
 });
}
function tick(){
 const d=new Date(),h=d.getHours(),m=String(d.getMinutes()).padStart(2,"0");
 $("#clock").textContent=String(h).padStart(2,"0")+":"+m;
 $("#date").textContent=new Intl.DateTimeFormat("es-ES",{weekday:"long",day:"numeric",month:"long"}).format(d);
 $("#greeting").textContent=(h<12?"Buenos días":h<20?"Buenas tardes":"Buenas noches")+".";
}
tick();setInterval(tick,10000);render();
function openModal(kind,title,callback){
 pending={kind,callback};$("#modalTitle").textContent=title;
 let fields="";
 if(kind==="note")fields='<label>Nota</label><input id="fText" placeholder="Escribe tu nota…" maxlength="180" autofocus>';
 if(kind==="reminder")fields='<label>Recordatorio</label><input id="fText" placeholder="¿Qué necesitas recordar?" maxlength="120"><label>Cuándo (opcional)</label><input id="fMeta" placeholder="Mañana, viernes, 15:00…">';
 if(kind==="link")fields='<label>Nombre</label><input id="fName" placeholder="Nombre del sitio"><label>Dirección web</label><input id="fUrl" placeholder="https://ejemplo.com"><label>Icono o inicial (opcional)</label><input id="fIcon" placeholder="↗" maxlength="3">';
 if(kind==="section")fields='<label>Nombre de la sección</label><input id="fName" placeholder="Por ejemplo: DESIGN"><label>Icono (opcional)</label><input id="fIcon" placeholder="✧" maxlength="3">';
 $("#modalFields").innerHTML=fields;$("#modalBackdrop").classList.add("open");
 setTimeout(()=>$("#modalFields input")?.focus(),50);
}
function closeModal(){$("#modalBackdrop").classList.remove("open");pending=null}
$("#cancelModal").onclick=closeModal;
$("#modalBackdrop").onclick=e=>{if(e.target.id==="modalBackdrop")closeModal()};
$("#saveModal").onclick=()=>{
 if(!pending)return;const k=pending.kind,cb=pending.callback;
 if(k==="note"||k==="reminder"){const text=$("#fText").value.trim();if(!text)return toast("Escribe algo primero");cb(k==="note"?{text,done:false}:{text,meta:$("#fMeta").value.trim(),done:false})}
 else if(k==="link"){const name=$("#fName").value.trim();let url=$("#fUrl").value.trim();if(!name||!url)return toast("Completa el nombre y la dirección");if(!/^[a-zA-Z][a-zA-Z\d+.-]*:/.test(url))url="https://"+url;try{new URL(url)}catch(e){return toast("La dirección no parece válida")}cb({name,url,icon:$("#fIcon").value.trim()||name[0].toUpperCase()})}
 else if(k==="section"){const name=$("#fName").value.trim();if(!name)return toast("Escribe un nombre");cb({name,icon:$("#fIcon").value.trim()||"✧",items:[]})}
 closeModal();render();toast("Guardado");
};
document.querySelectorAll("[data-add]").forEach(b=>b.onclick=()=>{const t=b.dataset.add;openModal(t,t==="note"?"Añadir nota":t==="reminder"?"Nuevo recordatorio":"Añadir enlace",item=>{snapshot();if(t==="build"||t==="daily")state[t].push(item);else state[t].push(item);persist()})});
$("#newSection").onclick=()=>openModal("section","Crear sección",s=>{snapshot();state.sections.push(s);persist()});
$("#workspaceName").textContent = PZ.workspace || "Personal";
$("#workOptions").innerHTML = "";
(PZ.workspaces||[]).forEach(function(name){
  const b=document.createElement("button"); b.dataset.work=name;
  b.textContent=name === PZ.workspace ? "✓ "+name : name;
  $("#workOptions").append(b);
});
const createWork=document.createElement("button");
createWork.dataset.work="create"; createWork.textContent="＋ Gestionar espacios…";
$("#workOptions").append(createWork);
$("#workBtn").onclick=()=>$("#workOptions").classList.toggle("open");
document.querySelectorAll("[data-work]").forEach(b=>b.onclick=()=>{
  toast("Cambia de espacio desde el menú de PedroZilla.");
  $("#workOptions").classList.remove("open");
});
document.addEventListener("click",e=>{if(!e.target.closest(".work-menu"))$("#workOptions").classList.remove("open")});
$("#search").addEventListener("keydown",e=>{if(e.key==="Enter"){
  const q=e.target.value.trim(); if(!q)return;
  const looksLikeUrl=/^https?:\/\//i.test(q)||(/^[\w-]+(\.[\w-]+)+(\/.*)?$/i.test(q)&&!q.includes(" "));
  const target=looksLikeUrl?(/^https?:\/\//i.test(q)?q:"https://"+q):PZ.searchTemplate.replace("{query}",encodeURIComponent(q));
  location.href = target;
}});
$("#search").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll(".link-item").forEach(el=>{el.style.display=!q||el.textContent.toLowerCase().includes(q)?"":"none"})});
$("#undoBtn").onclick=()=>{if(!undoStack.length)return toast("Nada que deshacer");redoStack.push(JSON.stringify(state));state=JSON.parse(undoStack.pop());persist();render();toast("Cambio deshecho")};
$("#redoBtn").onclick=()=>{if(!redoStack.length)return toast("Nada que rehacer");undoStack.push(JSON.stringify(state));state=JSON.parse(redoStack.pop());persist();render();toast("Cambio restaurado")};
$("#historyBtn").onclick=()=>toast("El historial completo está disponible desde PedroZilla.");
$("#shortcutsBtn").onclick=()=>toast("Consejo: escribe en el buscador y pulsa Enter.");
$("#settingsBtn").onclick=()=>toast("Ajustes: menú Pedrozilla → HERRAMIENTAS → Ajustes");
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeModal();if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();$("#search").focus()}});
</script>
</body>
</html>
"""
