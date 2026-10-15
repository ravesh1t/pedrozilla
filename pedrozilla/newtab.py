"""Página de nueva pestaña (HTML generado, sin recursos externos)."""

from __future__ import annotations

import html as html_module

from .storage import SEARCH_ENGINES
from .utils import host_of, initial_letter, color_for

_TEMPLATE_DARK = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nueva pestaña</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; font-family: system-ui, "Segoe UI", Roboto, sans-serif;
    background: radial-gradient(circle at 50% 18%, #2b2d31 0%, #202124 55%, #1b1c1f 100%);
    color: #e8eaed; display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 34px; padding: 48px 24px;
  }
  .badge { display:flex; gap:8px; align-items:center; font-size:12px; color:#9aa0a6;
           background:#2b2d31; border:1px solid #3c4043; padding:4px 12px; border-radius:999px; }
  .dot { width:8px; height:8px; border-radius:50%; background:#8ab4f8; }
  h1 { margin:0; font-size:42px; font-weight:400; letter-spacing:-.5px; }
  h1 span { color:#8ab4f8; }
  #clock { font-size:13px; color:#9aa0a6; margin-top:-22px; }
  form { width:min(620px, 92vw); }
  input[type=search] {
    width:100%; padding:15px 22px; font-size:16px; border-radius:999px;
    background:#303134; border:1px solid #3c4043; color:#e8eaed; outline:none;
  }
  input[type=search]:focus { border-color:#8ab4f8; box-shadow:0 1px 8px rgba(138,180,248,.25); }
  .hint { font-size:12px; color:#9aa0a6; text-align:center; margin-top:10px; }
  .bookmarks { width:min(880px, 94vw); }
  .bookmarks h2 { font-size:12px; text-transform:uppercase; letter-spacing:1.2px;
                  color:#9aa0a6; font-weight:600; margin:0 0 14px; text-align:center; }
  .grid { display:flex; flex-wrap:wrap; gap:12px; justify-content:center; }
  a.card {
    display:flex; align-items:center; gap:10px; text-decoration:none; color:#e8eaed;
    background:#292a2d; border:1px solid #3c4043; border-radius:12px; padding:10px 16px;
    font-size:13px; max-width:220px; transition:transform .12s, border-color .12s;
  }
  a.card:hover { transform:translateY(-2px); border-color:#8ab4f8; }
  .ico { width:26px; height:26px; border-radius:50%; display:grid; place-items:center;
         font-size:13px; font-weight:600; color:#202124; flex:none; }
  .meta { display:flex; flex-direction:column; overflow:hidden; }
  .meta small { color:#9aa0a6; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .meta span { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  footer { font-size:11px; color:#5f6368; }
</style>
</head>
<body>
  <div class="badge"><span class="dot"></span>__BRAND__ · motor Chromium __ENGINE_NAME__</div>
  <h1>__GREETING__<span>.</span></h1>
  <div id="clock"></div>
  <form onsubmit="return go(event)">
    <input id="q" type="search" placeholder="Buscar en __ENGINE_NAME__ o escribir una dirección" autofocus autocomplete="off">
    <div class="hint">Pulsa <b>Enter</b> para ir · <b>Ctrl+T</b> nueva pestaña · <b>Ctrl+L</b> barra de direcciones</div>
  </form>
  __BOOKMARKS__
  <footer>__FOOTER__</footer>
<script>
  const ENGINE = "__SEARCH_TEMPLATE__";
  function go(event) {
    event.preventDefault();
    const value = document.getElementById('q').value.trim();
    if (!value) return false;
    window.location.href = lookLikeUrl(value) ? withScheme(value)
                                              : ENGINE.replace('{query}', encodeURIComponent(value));
    return false;
  }
  function lookLikeUrl(text) {
    if (/\\s/.test(text)) return false;
    if (/^(https?|file|ftp|about):/i.test(text)) return true;
    if (/^(localhost|127\\.0\\.0\\.1|0\\.0\\.0\\.0)(:\\d+)?/i.test(text)) return true;
    return /^[^\\s/]+\\.[a-zA-Z]{2,}(:\\d+)?(\\/|$)/.test(text);
  }
  function withScheme(text) {
    return /^[a-zA-Z][a-zA-Z0-9+.\\-]*:/.test(text) ? text : 'http://' + text;
  }
  function paintClock() {
    const now = new Date();
    document.getElementById('clock').textContent =
      now.toLocaleDateString('es-ES', {weekday:'long', day:'numeric', month:'long'}) +
      ' · ' + now.toLocaleTimeString('es-ES', {hour:'2-digit', minute:'2-digit'});
  }
  paintClock();
  setInterval(paintClock, 15000);
</script>
</body>
</html>
"""

_TEMPLATE_LIGHT = (
    _TEMPLATE_DARK.replace(
        "background: radial-gradient(circle at 50% 18%, #2b2d31 0%, #202124 55%, #1b1c1f 100%);",
        "background: linear-gradient(160deg, #ffffff 0%, #eef2fb 60%, #e6ecf9 100%);",
    )
    .replace("color-scheme: dark", "color-scheme: light")
    .replace("color: #e8eaed;", "color: #202124;")
    .replace("background:#303134; border:1px solid #3c4043; color:#e8eaed;",
             "background:#f1f3f4; border:1px solid #dadce0; color:#202124;")
    .replace("background:#2b2d31; border:1px solid #3c4043;", "background:#f1f3f4; border:1px solid #dadce0;")
    .replace("background:#292a2d; border:1px solid #3c4043;", "background:#ffffff; border:1px solid #dadce0;")
    .replace("color:#9aa0a6", "color:#5f6368")
    .replace("#8ab4f8", "#1a73e8")
    .replace("color:#202124; flex:none;", "color:#ffffff; flex:none;")
    .replace("color:#5f6368;", "color:#80868b;")
)


def _bookmarks_html(bookmarks: list[dict]) -> str:
    if not bookmarks:
        return (
            '<div class="bookmarks"><h2>Marcadores</h2>'
            '<div class="grid" style="color:#9aa0a6;font-size:12px">'
            "Aún no hay marcadores. Pulsa la estrella en la barra de direcciones para guardar una página."
            "</div></div>"
        )

    cards = []
    for item in bookmarks[:16]:
        url = html_module.escape(str(item.get("url", "")), quote=True)
        title = html_module.escape(str(item.get("title", "")) or url)
        host = html_module.escape(host_of(str(item.get("url", ""))) or url)
        letter = html_module.escape(initial_letter(str(item.get("title", "")) or url))
        color = color_for(str(item.get("url", "")))
        cards.append(
            f'<a class="card" href="{url}" title="{url}">'
            f'<span class="ico" style="background:{color}">{letter}</span>'
            f'<span class="meta"><span>{title}</span><small>{host}</small></span></a>'
        )
    return (
        '<div class="bookmarks"><h2>Marcadores</h2><div class="grid">'
        + "".join(cards)
        + "</div></div>"
    )


def new_tab_html(
    search_template: str,
    engine_key: str,
    theme: str = "dark",
    bookmarks: list[dict] | None = None,
    footer: str = "Navegador basado en Chromium (Qt WebEngine)",
    brand: str = "Pedrozilla",
) -> str:
    """Devuelve el HTML de la página de nueva pestaña."""
    engine_name = SEARCH_ENGINES.get(engine_key, ("la web", ""))[0]
    template = _TEMPLATE_LIGHT if (theme or "").lower() == "light" else _TEMPLATE_DARK

    greeting_pool = ("Hola", "Bienvenido", "Listo para navegar")
    greeting = greeting_pool[len(bookmarks or []) % len(greeting_pool)]

    return (
        template.replace("__BRAND__", html_module.escape(brand))
        .replace("__ENGINE_NAME__", html_module.escape(engine_name))
        .replace("__SEARCH_TEMPLATE__", search_template.replace('"', "%22"))
        .replace("__BOOKMARKS__", _bookmarks_html(bookmarks or []))
        .replace("__GREETING__", greeting)
        .replace("__FOOTER__", html_module.escape(footer))
    )
