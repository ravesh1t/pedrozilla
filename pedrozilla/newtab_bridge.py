"""Puente entre la página de nueva pestaña y el backend del navegador.

La nueva pestaña es HTML normal, así que no puede llamar a Python directamente.
Qt WebEngine expone este objeto por `QWebChannel` y el JavaScript lo usa como
`window.pedrozilla` (ver `newtab.py`).
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Slot


class NewTabBridge(QObject):
    """Operaciones que la nueva pestaña puede pedirle al navegador."""

    def __init__(self, context) -> None:
        super().__init__()
        self._context = context

    # -- accesos rápidos ----------------------------------------------------
    @Slot(str, str, result=bool)
    def addShortcut(self, title: str, url: str) -> bool:
        return self._context.shortcuts.add(title, url)

    @Slot(str, result=bool)
    def removeShortcut(self, url: str) -> bool:
        return self._context.shortcuts.remove(url)

    @Slot("QStringList")
    def reorderShortcuts(self, urls: list[str]) -> None:
        self._context.shortcuts.reorder(list(urls))

    @Slot(result="QVariantList")
    def getShortcuts(self) -> list[dict[str, Any]]:
        return self._context.shortcuts.items()

    # -- marcadores e historial --------------------------------------------
    @Slot(str, str, result=bool)
    def toggleBookmark(self, title: str, url: str) -> bool:
        return self._context.bookmarks.toggle(title, url)

    @Slot(result="QVariantList")
    def getBookmarks(self) -> list[dict[str, Any]]:
        return self._context.bookmarks.items()

    @Slot(result="QVariantList")
    def getHistory(self) -> list[dict[str, Any]]:
        return self._context.history.entries()

    # -- sugerencias --------------------------------------------------------
    @Slot(str, int, result="QStringList")
    def getSuggestions(self, query: str, limit: int = 6) -> list[str]:
        """Sugerencias sin conexión a partir del historial (y de los accesos)."""
        query = (query or "").strip().lower()
        if not query:
            return []
        found: list[str] = []
        for url in self._context.history.completions(query, limit):
            if url not in found:
                found.append(url)
        if len(found) < limit:
            for item in self._context.shortcuts.items():
                title = str(item.get("title", ""))
                url = str(item.get("url", ""))
                if query in title.lower() or query in url.lower():
                    if title and title not in found:
                        found.append(title)
                if len(found) >= limit:
                    break
        return found[:limit]
