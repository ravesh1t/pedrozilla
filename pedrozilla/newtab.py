"""Página de nueva pestaña: diseño adjuntado por el usuario e integrado en Pedrozilla.

La plantilla HTML vive en `newtab_template.py`. Este módulo solo inyecta los
datos del perfil (atajos, historial, motor de búsqueda, espacios y ajustes) y
el cliente de QWebChannel para que los cambios se guarden en `settings.json`.
"""
from __future__ import annotations

import html as html_module
import json
import sys
from pathlib import Path

from .newtab_template import TEMPLATE
from .storage import SEARCH_ENGINES


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


def new_tab_html(
    search_template: str,
    engine_key: str,
    theme: str = "modern",
    bookmarks: list[dict] | None = None,
    shortcuts: list[dict] | None = None,
    history: list[dict] | None = None,
    accent: str = "#ff7a32",
    footer: str = "",
    brand: str = "Pedrozilla",
    newtab_prefs: dict | None = None,
    workspaces: dict | None = None,
    active_workspace: str | None = None,
) -> str:
    """Genera la nueva pestaña con los datos actuales del perfil."""
    engine_name = SEARCH_ENGINES.get(engine_key, ("la web", ""))[0]

    def as_json(value) -> str:
        return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")

    def as_link(item: dict) -> dict | None:
        name = str(item.get("title") or item.get("name") or "").strip()
        url = str(item.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return None
        glyph = str(item.get("icon") or (name[:1].upper() if name else "↗"))
        return {"name": name or url, "url": url, "icon": glyph[:3]}

    shortcut_links: list[dict] = []
    candidates = list(shortcuts or []) + list(bookmarks or [])
    for item in candidates:
        link = as_link(item)
        if link is not None and link not in shortcut_links:
            shortcut_links.append(link)
        if len(shortcut_links) >= 12:
            break

    recent_links: list[dict] = []
    for item in (history or [])[:12]:
        link = as_link(item)
        if link is not None and link not in recent_links:
            recent_links.append(link)

    workspaces = workspaces or {}
    if active_workspace and active_workspace in workspaces:
        info = workspaces[active_workspace]
        active_name = str(info.get("name") or active_workspace)
    else:
        active_name = active_workspace or "Personal"
    workspace_names: list[str] = []
    for info in workspaces.values():
        name = str(info.get("name") or "")
        if name and name not in workspace_names:
            workspace_names.append(name)

    config = {
        "prefs": newtab_prefs or {},
        "searchTemplate": search_template,
        "engineName": engine_name,
        "shortcuts": shortcut_links,
        "recent": recent_links,
        "workspace": active_name,
        "workspaces": workspace_names,
        "footer": footer,
    }

    return (
        TEMPLATE.replace("__QWEBCHANNEL_JS__", _QWEBCHANNEL_JS)
        .replace("__CONFIG_JSON__", as_json(config))
        .replace("__BRAND__", html_module.escape(brand))
        .replace("__ACCENT__", html_module.escape(accent or "#e58b36"))
        .replace("__WORKSPACE__", html_module.escape(active_name))
    )
