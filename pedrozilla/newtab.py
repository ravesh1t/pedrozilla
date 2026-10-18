"""Página de nueva pestaña (HTML generado, sin recursos externos)."""
from __future__ import annotations

import html as html_module
import sys
from pathlib import Path

from .storage import SEARCH_ENGINES
from .utils import host_of, initial_letter, color_for


def _load_qwebchannel_js() -> str:
    """Carga qwebchannel.js tanto en modo normal como congelado (PyInstaller)."""
    # Modo congelado por PyInstaller (onefile)
    if getattr(sys, "frozen", False):
        meipass = Path(sys._MEIPASS)
        # Buscar en el layout usado con --add-data (pedrozilla\data)
        candidates = [
            meipass / "pedrozilla" / "data" / "qwebchannel.js",
            meipass / "pedrozilla" / "qwebchannel.js",
            meipass / "data" / "qwebchannel.js",
            meipass / "qwebchannel.js",
        ]
        for p in candidates:
            if p.exists():
                return p.read_text(encoding="utf-8")
    # Modo desarrollo
    candidates = [
        Path(__file__).with_name("data") / "qwebchannel.js",
        Path(__file__).parent / "data" / "qwebchannel.js",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    # Fallback: cargar como paquete recurso
    try:
        import importlib.resources as res

        if res.files("pedrozilla").joinpath("data", "qwebchannel.js").is_file():
            return res.files("pedrozilla").joinpath("data", "qwebchannel.js").read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


#: Cliente JS de Qt WebChannel, embebido para funcionar sin conexión (LGPL-3.0, Qt Company).
_QWEBCHANNEL_JS = _load_qwebchannel_js()


def _hour_greeting() -> str:
    from datetime import datetime

    h = datetime.now().hour
    if 6 <= h < 12:
        return "Buenos días"
    if 12 <= h < 20:
        return "Buenas tardes"
    return "Buenas noches"


_LOGO_SVG = '<svg width="14" height="14" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><circle cx="32" cy="32" r="30" fill="var(--accent)"/><text x="32" y="38" font-size="34" text-anchor="middle" fill="#202124" font-family="system-ui,Segoe UI,Roboto,Arial">P</text></svg>'
_DEF_SHORTCUTS = [
    {"title": "YouTube", "url": "https://www.youtube.com/"},
    {"title": "Wikipedia", "url": "https://es.wikipedia.org/"},
    {"title": "GitHub", "url": "https://github.com/"},
    {"title": "Gmail", "url": "https://mail.google.com/"},
    {"title": "Google Maps", "url": "https://www.google.com/maps"},
    {"title": "DuckDuckGo", "url": "https://duckduckgo.com/"},
]


def _shortcuts_html(shortcuts: list[dict]) -> str:
    items = list(shortcuts or [])[:16]
    if not items:
        items = _DEF_SHORTCUTS
    cards = []
    for item in items:
        url = html_module.escape(str(item.get("url", "")), quote=True)
        title = html_module.escape(str(item.get("title", "")) or url)
        host = html_module.escape(host_of(str(item.get("url", ""))) or url)
        letter = html_module.escape(initial_letter(str(item.get("title", "")) or url))
        color = color_for(str(item.get("url", "")))
        cards.append(
            '<div class="scard" data-url="%(url)s" draggable="true" tabindex="0" role="button" aria-label="Acceso a %(title)s">'
            '<a class="scard-link" href="%(url)s" title="%(url)s">'
            '<span class="ico" style="background:%(color)s">%(letter)s</span>'
            '<span class="sname">%(title)s</span>'
            '</a>'
            '<button class="sremove" type="button" title="Quitar acceso" aria-label="Quitar %(title)s">×</button>'
            '</div>'
            % {"url": url, "title": title, "host": host, "letter": letter, "color": color}
        )
    return (
        '<section class="shortcuts" aria-label="Accesos rápidos">'
        '<div class="sgrid" id="sgrid">' + "".join(cards) + '</div>'
        '<div class="sactions"><button type="button" id="sadd">Añadir acceso</button></div>'
        '</section>'
    )


_TEMPLATE_DARK = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nueva pestaña</title>
<style>
:root {
  color-scheme: dark;
  --bg1:#1b1c1f;
  --bg2:#202124;
  --bg3:#2b2d31;
  --card:#292a2d;
  --border:#3c4043;
  --text:#e8eaed;
  --text2:#9aa0a6;
  --accent:__ACCENT__;
  --shadow:0 6px 18px rgba(0,0,0,.25);
}
* { box-sizing:border-box; font-family: system-ui,"Segoe UI",Roboto,Segoe UI Variable,Arial,sans-serif; }
html,body { height:100%; margin:0; }
body {
  min-height:100vh;
  background: radial-gradient(1200px 600px at 50% 10%, rgba(255,255,255,.04), transparent 60%), radial-gradient(circle at 50% 0%, var(--bg3) 0%, var(--bg2) 55%, var(--bg1) 100%);
  color:var(--text);
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:28px;
  padding:48px 24px;
  text-rendering:optimizeLegibility;
  -webkit-font-smoothing:antialiased;
}
.header { display:flex; align-items:center; gap:10px; color:var(--text2); font-size:12px; }
.logo { display:flex; align-items:center; gap:8px; background:var(--bg3); border:1px solid var(--border); padding:4px 10px; border-radius:999px; }
.logo svg { width:14px; height:14px; display:block; }
.brand { color:var(--text); opacity:.9; }
.engine { opacity:.8; }
.greet { margin:0; font-size:36px; font-weight:400; letter-spacing:-.4px; opacity:.98; }
.clock { display:flex; flex-direction:column; align-items:center; gap:4px; margin-top:-10px; }
#time { font-size:44px; font-weight:400; letter-spacing:-1px; }
#date { font-size:13px; color:var(--text2); text-transform:capitalize; }
.searchwrap { width:min(720px, 92vw); position:relative; }
#q { width:100%; padding:14px 52px 14px 20px; font-size:16px; border-radius:999px; background:var(--card); border:1px solid var(--border); color:var(--text); outline:none; transition: border-color .12s, box-shadow .12s; }
#q:focus { border-color:var(--accent); box-shadow:0 1px 10px color-mix(in srgb, var(--accent) 22%, transparent); }
.sicon { position:absolute; right:14px; top:50%; transform:translateY(-50%); opacity:.6; pointer-events:none; }
.suggest { position:absolute; left:10px; right:10px; top:calc(100% + 8px); background:var(--card); border:1px solid var(--border); border-radius:12px; box-shadow:var(--shadow); display:none; z-index:5; }
.suggest.show { display:block; }
.suggest div { padding:8px 14px; font-size:13px; color:var(--text); cursor:pointer; }
.suggest div:hover, .suggest div.active { background:color-mix(in srgb, var(--accent) 14%, var(--card)); }
.shortcuts { width:min(860px, 94vw); display:flex; flex-direction:column; gap:12px; }
.sgrid { display:flex; flex-wrap:wrap; gap:10px; justify-content:center; }
.scard { position:relative; display:flex; align-items:center; gap:10px; background:var(--card); border:1px solid var(--border); border-radius:12px; padding:8px 12px; min-width:160px; max-width:220px; transition: transform .12s ease, border-color .12s ease, box-shadow .12s ease; animation: fadein .16s ease; }
.scard[draggable="true"] { cursor:grab; }
.scard.dragover { border-color:var(--accent); box-shadow:0 0 0 2px color-mix(in srgb, var(--accent) 22%, transparent); }
.scard:hover { transform:translateY(-2px); border-color:var(--accent); }
.scard-link { display:flex; align-items:center; gap:10px; text-decoration:none; color:var(--text); flex:1; min-width:0; }
.ico { width:26px; height:26px; border-radius:50%; display:grid; place-items:center; font-size:13px; font-weight:600; color:#202124; flex:none; }
.sname { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-size:13px; }
.sremove { position:absolute; right:4px; top:4px; background:transparent; border:none; color:var(--text2); font-size:14px; line-height:1; padding:2px 6px; border-radius:8px; cursor:pointer; display:none; }
.scard:hover .sremove { display:block; }
.sremove:hover { background:color-mix(in srgb, var(--accent) 18%, transparent); color:var(--text); }
.sactions { display:flex; justify-content:center; }
#sadd { background:transparent; border:1px dashed color-mix(in srgb, var(--text2) 40%, transparent); color:var(--text2); border-radius:999px; padding:6px 12px; font-size:12px; cursor:pointer; }
#sadd:hover { color:var(--text); border-color:var(--accent); }
footer { font-size:11px; color:var(--text2); opacity:.7; }
@keyframes fadein { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }
@media (max-width:680px) { #time { font-size:34px; } .greet { font-size:28px; } }
</style>
</head>
<body>
  <header class="header">
    <div class="logo">__LOGO__<span class="brand">__BRAND__</span><span class="engine">· __ENGINE_NAME__</span></div>
  </header>
  <h1 class="greet">__GREETING__</h1>
  <div class="clock">
    <div id="time">--:--</div>
    <div id="date">-</div>
  </div>
  <div class="searchwrap">
    <input id="q" type="search" placeholder="Buscar en __ENGINE_NAME__ o escribir una dirección" autocomplete="off" spellcheck="false">
    <svg class="sicon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
    <div class="suggest" id="suggest"></div>
  </div>
  __SHORTCUTS__
  <footer>__FOOTER__</footer>
<script>
__QWEBCHANNEL_JS__
</script>
<script>
const ENGINE="__SEARCH_TEMPLATE__";
const ACCENT="__ACCENT__";
// Puente con el navegador: si la página corre dentro de Pedrozilla, QWebChannel
// publica el objeto `pedrozilla` (añadir/quitar/reordenar accesos y sugerencias).
window.pedrozilla = undefined;
if (typeof qt !== 'undefined' && qt.webChannelTransport) {
  new QWebChannel(qt.webChannelTransport, function(channel){
    window.pedrozilla = channel.objects.pedrozilla;
  });
}
document.documentElement.style.setProperty('--accent', ACCENT);
function paintClock(){
  const now=new Date();
  document.getElementById('time').textContent=now.toLocaleTimeString('es-ES',{hour:'2-digit',minute:'2-digit'});
  document.getElementById('date').textContent=now.toLocaleDateString('es-ES',{weekday:'long',day:'numeric',month:'long'});
}
paintClock(); setInterval(paintClock,15000);
function looksLikeUrl(t){ if(/\s/.test(t))return false; if(/^(https?|file|ftp|about):/i.test(t))return true; if(/^(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?/i.test(t))return true; return /^[^\s/]+\.[a-zA-Z]{2,}(:\d+)?(\/|$)/.test(t); }
function withScheme(t){ return /^[a-zA-Z][a-zA-Z0-9+\.\-]*:/.test(t)?t:'http://'+t; }
function go(v){ v=v.trim(); if(!v)return; location.href=looksLikeUrl(v)?withScheme(v):ENGINE.replace('{query}',encodeURIComponent(v)); }
const q=document.getElementById('q');
let sugIdx=-1;
function updateSel(items){ items.forEach((it,i)=>it.classList.toggle('active',i===sugIdx)); }
q.addEventListener('keydown',e=>{
  const sug=document.getElementById('suggest');
  const items=[...sug.querySelectorAll('div')];
  if(e.key==='ArrowDown'){ e.preventDefault(); sugIdx=(sugIdx+1)%Math.max(1,items.length); updateSel(items); return; }
  if(e.key==='ArrowUp'){ e.preventDefault(); sugIdx=(sugIdx-1+items.length)%Math.max(1,items.length); updateSel(items); return; }
  if(e.key==='Enter'){ if(sugIdx>=0 && items[sugIdx]){ e.preventDefault(); q.value=items[sugIdx].textContent; sug.classList.remove('show'); sugIdx=-1; go(q.value); return; } e.preventDefault(); go(q.value); return; }
  if(e.key==='Escape'){ sug.classList.remove('show'); sugIdx=-1; }
});
q.addEventListener('input',()=>{
  const v=q.value.trim();
  if(v.length<2){ document.getElementById('suggest').classList.remove('show'); sugIdx=-1; return; }
  fetch('https://duckduckgo.com/ac/?q='+encodeURIComponent(v)+'&type=thought').then(r=>r.json()).then(list=>{
    const sug=document.getElementById('suggest');
    sug.innerHTML=''; sugIdx=-1;
    (list||[]).slice(0,6).forEach(x=>{
      const d=document.createElement('div');
      d.textContent=x.phrase||x;
      d.onclick=()=>{ q.value=d.textContent; sug.classList.remove('show'); go(q.value); };
      sug.appendChild(d);
    });
    if(sug.children.length) sug.classList.add('show'); else sug.classList.remove('show');
  }).catch(()=>{ document.getElementById('suggest').classList.remove('show'); });
});
let sgrid=document.getElementById('sgrid');
document.getElementById('sadd').onclick=async()=>{
  const title=prompt('Nombre del acceso (opcional):','');
  const url=prompt('URL:','https://');
  if(!url||!url.trim())return;
  if(window.pedrozilla && window.pedrozilla.addShortcut){
    await window.pedrozilla.addShortcut(title||url.trim(), url.trim());
    location.reload();
  }
};
sgrid.addEventListener('click',e=>{
  if(e.target.classList.contains('sremove')){
    e.preventDefault(); e.stopPropagation();
    const card=e.target.closest('.scard'); const u=card.dataset.url;
    if(window.pedrozilla && window.pedrozilla.removeShortcut){ window.pedrozilla.removeShortcut(u).then(()=>location.reload()); }
    return;
  }
});
let dragSrc=null;
sgrid.addEventListener('dragstart',e=>{ const c=e.target.closest('.scard'); if(!c)return; dragSrc=c; e.dataTransfer.effectAllowed='move'; e.dataTransfer.setData('text/plain',c.dataset.url); });
sgrid.addEventListener('dragover',e=>{ e.preventDefault(); const c=e.target.closest('.scard'); if(c && c!==dragSrc) c.classList.add('dragover'); });
sgrid.addEventListener('dragleave',e=>{ const c=e.target.closest('.scard'); if(c) c.classList.remove('dragover'); });
sgrid.addEventListener('drop',e=>{ e.preventDefault(); const c=e.target.closest('.scard'); if(c && c!==dragSrc){ sgrid.insertBefore(dragSrc,c.nextSibling); syncOrder(); } [...sgrid.querySelectorAll('.scard')].forEach(x=>x.classList.remove('dragover')); });
sgrid.addEventListener('dragend',e=>{ [...sgrid.querySelectorAll('.scard')].forEach(x=>x.classList.remove('dragover')); dragSrc=null; });
function syncOrder(){
  const urls=[...sgrid.querySelectorAll('.scard')].map(x=>x.dataset.url);
  if(window.pedrozilla && window.pedrozilla.reorderShortcuts) window.pedrozilla.reorderShortcuts(urls);
}
</script>
</body>
</html>
"""


def new_tab_html(
    search_template: str,
    engine_key: str,
    theme: str = "dark",
    bookmarks: list[dict] | None = None,
    shortcuts: list[dict] | None = None,
    history: list[dict] | None = None,
    accent: str = "#8ab4f8",
    footer: str = "",
    brand: str = "Pedrozilla",
) -> str:
    engine_name = SEARCH_ENGINES.get(engine_key, ("la web", ""))[0]
    template = _TEMPLATE_DARK
    greeting = _hour_greeting()

    return (
        template.replace("__BRAND__", html_module.escape(brand))
        .replace("__ENGINE_NAME__", html_module.escape(engine_name))
        .replace("__SEARCH_TEMPLATE__", search_template.replace('"', "%22"))
        .replace("__QWEBCHANNEL_JS__", _QWEBCHANNEL_JS)
        .replace("__SHORTCUTS__", _shortcuts_html(shortcuts or _DEF_SHORTCUTS))
        .replace("__GREETING__", greeting)
        .replace("__FOOTER__", html_module.escape(footer) if footer else "")
        .replace("__ACCENT__", html_module.escape(accent or "#8ab4f8"))
        .replace("__LOGO__", _LOGO_SVG)
    )
