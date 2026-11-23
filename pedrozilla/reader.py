"""Modo lectura para Pedrozilla.

No usa dependencias externas ni servicios de terceros: extrae el contenido
principal del DOM ya cargado con heurísticas locales y lo muestra en una capa
superpuesta. La página original no se modifica.

Qt WebEngine no ofrece una API de "modo lectura", así que esta implementación
es JavaScript inyectado. Si no se identifica un artículo con suficiente texto,
la función lo comunica y la página queda intacta.
"""

from __future__ import annotations

# Los marcadores se sustituyen en reader_script(). Se evita f-string porque el
# JavaScript contiene llaves.
_READER_JS = r"""
(function(){
  "use strict";
  var existing = document.getElementById("__PZ_ID__");
  if (existing) { existing.remove(); return "closed"; }

  function cleanText(node){
    return ((node && (node.innerText || node.textContent)) || "").replace(/\s+/g, " ").trim();
  }
  function badClass(node){
    var value = ((node.className && node.className.baseVal) || node.className || "") + " " + (node.id || "");
    return /nav|aside|footer|header|comment|sidebar|menu|banner|advert|promo|related|share/i.test(value);
  }

  var selectors = "article, main, [role=main], .post, .entry-content, .article-content, .article, #content, .content";
  var candidates = Array.prototype.slice.call(document.querySelectorAll(selectors));
  var best = null;
  var bestScore = 0;
  candidates.forEach(function(node){
    var text = cleanText(node);
    var score = text.length * (badClass(node) ? 0.35 : 1);
    if (score > bestScore) { bestScore = score; best = node; }
  });

  // Segunda pasada: several párrafos largos juntos suelen ser el artículo.
  if (!best || bestScore < 220) {
    var fallback = document.createElement("div");
    Array.prototype.slice.call(document.querySelectorAll("p")).forEach(function(p){
      if (cleanText(p).length >= 60) fallback.appendChild(p.cloneNode(true));
    });
    if (cleanText(fallback).length >= 220) { best = fallback; }
  }
  if (!best || cleanText(best).length < 220) { return "no-article"; }

  var dark = "__PZ_THEME__" === "dark";
  var host = document.createElement("div");
  host.id = "__PZ_ID__";
  host.setAttribute("style",
    "position:fixed;inset:0;z-index:2147483647;overflow:auto;" +
    "background:" + (dark ? "#15171c" : "#f7f5f0") + ";" +
    "color:" + (dark ? "#e8e6e1" : "#202327") + ";" +
    "font-family:Georgia,'Times New Roman',serif;" +
    "font-size:" + "__PZ_SIZE__" + "px;line-height:1.75;padding:24px 16px 80px;"
  );

  var bar = document.createElement("div");
  bar.setAttribute("style",
    "position:sticky;top:0;z-index:2;display:flex;justify-content:space-between;" +
    "align-items:center;gap:12px;max-width:" + "__PZ_WIDTH__" + "px;margin:0 auto 28px;" +
    "padding:10px 12px;border-radius:10px;" +
    "background:" + (dark ? "#20242b" : "#ffffff") + ";" +
    "font-family:system-ui,sans-serif;font-size:12px;"
  );
  var label = document.createElement("span");
  label.textContent = "Modo lectura · " + (document.title || "Página");
  label.setAttribute("style", "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;");
  var close = document.createElement("button");
  close.type = "button";
  close.textContent = "✕ Cerrar (Esc)";
  close.setAttribute("style",
    "flex:none;border:0;border-radius:8px;padding:7px 12px;cursor:pointer;" +
    "background:#ef8b28;color:#ffffff;font:inherit;font-weight:600;"
  );
  close.addEventListener("click", function(){ host.remove(); });
  bar.appendChild(label);
  bar.appendChild(close);
  host.appendChild(bar);

  var article = best.cloneNode(true);
  Array.prototype.slice.call(
    article.querySelectorAll("script,style,noscript,nav,aside,footer,header,form,iframe,button,svg,video,audio,select,input")
  ).forEach(function(node){ node.remove(); });
  Array.prototype.slice.call(article.querySelectorAll("*")).forEach(function(node){
    ["onclick", "onload", "onerror", "onmouseover", "onfocus"].forEach(function(attr){
      node.removeAttribute(attr);
    });
    if (node.hasAttribute("style")) {
      node.setAttribute("style", (node.getAttribute("style") || "")
        .replace(/position\s*:\s*(fixed|absolute)/gi, "")
        .replace(/z-index\s*:\s*\d+/gi, ""));
    }
  });
  article.setAttribute("style",
    "max-width:" + "__PZ_WIDTH__" + "px;margin:0 auto;word-wrap:break-word;" +
    "font-size:inherit;line-height:inherit;"
  );
  Array.prototype.slice.call(article.querySelectorAll("img")).forEach(function(img){
    img.setAttribute("style", "max-width:100%;height:auto;");
  });
  host.appendChild(article);

  function onKey(event){
    if (event.key === "Escape") {
      host.remove();
      document.removeEventListener("keydown", onKey, true);
    }
  }
  document.addEventListener("keydown", onKey, true);
  document.body.appendChild(host);
  window.scrollTo(0, 0);
  return "ok";
})()
"""

_PIP_JS = r"""
(function(){
  "use strict";
  var video = document.querySelector("video");
  if (!video) { return "sin-video"; }
  if (!document.pictureInPictureEnabled) { return "no-soportado"; }
  if (document.pictureInPictureElement === video) {
    document.exitPictureInPicture();
    return "salir";
  }
  try {
    video.requestPictureInPicture().then(
      function(){ return "ok"; },
      function(error){ return "error: " + (error && error.message ? error.message : "desconocido"); }
    );
    return "ok";
  } catch (error) {
    return "error: " + (error && error.message ? error.message : "desconocido");
  }
})()
"""


def reader_script(*, font_size: int = 19, width: int = 720, theme: str = "dark") -> str:
    """Devuelve el JavaScript del modo lectura con la configuración aplicada."""
    return (
        _READER_JS.replace("__PZ_ID__", "pedrozilla-reader")
        .replace("__PZ_THEME__", "dark" if theme == "dark" else "light")
        .replace("__PZ_SIZE__", str(int(font_size)))
        .replace("__PZ_WIDTH__", str(int(width)))
    )


def picture_in_picture_script() -> str:
    """Devuelve el JavaScript que solicita el PiP nativo de Chromium al primer vídeo."""
    return _PIP_JS
