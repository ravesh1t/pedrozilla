"""Iconos SVG en línea para el menú principal.

Se renderizan con QtSvg (incluido en PySide6), sin archivos externos ni
dependencias nuevas. Todos comparten el mismo estilo: trazo de 24×24, esquinas
redondeadas y color neutro que combina con los cuatro temas.
"""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PATHS = {
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "window": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/>',
    "folder": '<path d="M4 6h6l2 2h8v11H4z"/>',
    "save": '<path d="M5 4h11l3 3v13H5z"/><path d="M8 4v5h7V4M8 20v-6h8v6"/>',
    "pdf": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h4"/>',
    "print": '<path d="M7 9V4h10v5M6 18H4v-7h16v7h-2M7 14h10v7H7z"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "undo": '<path d="M9 8L5 12l4 4M5 12h8a5 5 0 0 1 0 10"/>',
    "redo": '<path d="M15 8l4 4-4 4M19 12h-8a5 5 0 0 0 0 10"/>',
    "cut": '<circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/><path d="M8 16L18 4M16 16L6 4"/>',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
    "paste": '<rect x="5" y="7" width="14" height="14" rx="2"/><path d="M9 7V5h6v2"/>',
    "select": '<rect x="4" y="4" width="16" height="16" rx="2" stroke-dasharray="3 2"/>',
    "find": '<circle cx="10.5" cy="10.5" r="5.5"/><path d="M15 15l5 5"/>',
    "reload": '<path d="M20 12a8 8 0 1 1-2.4-5.7M20 4v5h-5"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="1"/>',
    "reset": '<path d="M4 12a8 8 0 1 0 3-6.2M4 4v5h5"/>',
    "fullscreen": '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    "bookmark": '<path d="M6 3h12v18l-6-4-6 4z"/>',
    "source": '<path d="M9 8l-4 4 4 4M15 8l4 4-4 4"/>',
    "devtools": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18M7 5v4"/>',
    "reader": '<path d="M4 5h7a3 3 0 0 1 3 3v11a3 3 0 0 0-3-3H4zM20 5h-3a3 3 0 0 0-3 3v11a3 3 0 0 1 3-3h3z"/>',
    "split": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/>',
    "pip": '<rect x="3" y="5" width="18" height="14" rx="2"/><rect x="12" y="11" width="7" height="6" rx="1"/>',
    "history": '<path d="M4 12a8 8 0 1 0 3-6.2M4 4v5h5M12 8v4l3 2"/>',
    "trash": '<path d="M5 7h14M9 7V4h6v3M7 7l1 13h8l1-13"/>',
    "download": '<path d="M12 4v11m-4-4l4 4 4-4M5 20h14"/>',
    "back": '<path d="M15 6l-6 6 6 6"/>',
    "forward": '<path d="M9 6l6 6-6 6"/>',
    "home": '<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>',
    "tools": '<path d="M14 6a4 4 0 0 0-5 5l-5 5a2 2 0 0 0 3 3l5-5a4 4 0 0 0 5-5l-3 3-3-3z"/>',
    "extensions": '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
    "privacy": '<path d="M12 3l7 3v5c0 4.5-3 7.5-7 10-4-2.5-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .7-1.5 1.2-1.5 2.5M12 17h.01"/>',
    "update": '<path d="M20 12a8 8 0 1 1-2.4-5.7M20 4v5h-5M12 8v4l3 2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
}

_BY_LABEL = {
    "Nueva pestaña": "plus",
    "Nueva ventana": "window",
    "Nueva ventana privada": "privacy",
    "Abrir archivo local": "folder",
    "Guardar página como": "save",
    "Guardar como PDF": "pdf",
    "Imprimir": "print",
    "Cerrar pestaña": "close",
    "Salir": "close",
    "Deshacer": "undo",
    "Rehacer": "redo",
    "Cortar": "cut",
    "Copiar": "copy",
    "Pegar": "paste",
    "Seleccionar todo": "select",
    "Buscar en la página": "find",
    "Recargar": "reload",
    "Recargar sin caché": "reload",
    "Detener": "stop",
    "Aumentar zoom": "plus",
    "Reducir zoom": "minus",
    "Zoom original": "reset",
    "Zoom": "plus",
    "Pantalla completa": "fullscreen",
    "Barra de marcadores": "bookmark",
    "Ver código fuente": "source",
    "DevTools": "devtools",
    "Más": "tools",
    "Modo lectura": "reader",
    "Vista dividida": "split",
    "Vídeo en ventana flotante (PiP)": "pip",
    "Ver historial": "history",
    "Reabrir pestaña cerrada": "plus",
    "Navegación": "history",
    "Atrás": "back",
    "Adelante": "forward",
    "Página de inicio": "home",
    "Pestañas cerradas recientemente": "history",
    "Borrar datos de navegación": "trash",
    "Añadir marcador": "bookmark",
    "Administrar marcadores": "folder",
    "Abrir gestor de descargas": "download",
    "Abrir carpeta de descargas": "folder",
    "Espacios de trabajo": "folder",
    "Gestionar grupos": "tools",
    "Extensiones": "extensions",
    "Ajustes": "settings",
    "Privacidad y seguridad": "privacy",
    "Buscar actualizaciones": "update",
    "Acerca de Pedrozilla": "info",
}

_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{color}" stroke-width="1.7" stroke-linecap="round" '
    'stroke-linejoin="round">{body}</svg>'
)


@lru_cache(maxsize=128)
def menu_icon(label: str, color: str = "#6b7280") -> QIcon:
    """Devuelve el icono SVG asociado a una opción del menú principal."""
    key = label.replace("&", "").replace("…", "").strip()
    name = _BY_LABEL.get(key, key)
    body = _PATHS.get(name, _PATHS["info"])
    renderer = QSvgRenderer(_TEMPLATE.format(color=color, body=body).encode("utf-8"))
    image = QImage(20, 20, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QIcon(QPixmap.fromImage(image))
