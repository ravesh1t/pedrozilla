"""Persistencia del navegador: ajustes, historial, marcadores y sesión.

Todo se guarda como JSON en el directorio de configuración del usuario:
%APPDATA% y %LOCALAPPDATA% en Windows, directorios XDG en Linux.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from .utils import canonical_url

APP_NAME = "Pedrozilla"
APP_DIR_NAME = "pedrozilla"
HISTORY_LIMIT = 8000

SEARCH_ENGINES: dict[str, tuple[str, str]] = {
    "duckduckgo": ("DuckDuckGo", "https://duckduckgo.com/?q={query}"),
    "google": ("Google", "https://www.google.com/search?q={query}"),
    "brave": ("Brave", "https://search.brave.com/search?q={query}"),
    "bing": ("Bing", "https://www.bing.com/search?q={query}"),
    "ecosia": ("Ecosia", "https://www.ecosia.org/search?q={query}"),
    "wikipedia": ("Wikipedia (es)", "https://es.wikipedia.org/w/index.php?search={query}"),
    "youtube": ("YouTube", "https://www.youtube.com/results?search_query={query}"),
}

DEFAULT_SETTINGS: dict[str, Any] = {
    "search_engine": "duckduckgo",
    "homepage": "",
    "startup": "newtab",  # newtab | restore | homepage
    "download_dir": "",
    "ask_download_dir": False,
    "show_bookmarks_bar": True,
    "theme": "classic",  # classic | dark | light
    "default_zoom": 1.0,
    "user_agent": "",
    "javascript": True,
    "ignore_certificate_errors": False,
    # IDs de extensiones que el usuario dejó activas (las instaladas en el
    # perfil las recarga Qt en cada arranque, pero siempre desactivadas).
    "enabled_extensions": [],
}


def _app_dir(env_var: str, fallback: str) -> Path:
    base = os.environ.get(env_var) or os.path.expanduser(fallback)
    path = Path(base) / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    if os.name == "nt":
        # En Windows lo habitual es %APPDATA%; se respeta XDG_CONFIG_HOME si
        # el usuario lo tiene definido (por ejemplo, con MSYS2 o Cygwin).
        base = os.environ.get("XDG_CONFIG_HOME")
        if base:
            return _app_dir("XDG_CONFIG_HOME", "~/.config")
        return _app_dir("APPDATA", "~/AppData/Roaming")
    return _app_dir("XDG_CONFIG_HOME", "~/.config")


def data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("XDG_DATA_HOME")
        if base:
            return _app_dir("XDG_DATA_HOME", "~/.local/share")
        return _app_dir("LOCALAPPDATA", "~/AppData/Local")
    return _app_dir("XDG_DATA_HOME", "~/.local/share")


def default_download_dir() -> Path:
    downloads = Path.home() / "Downloads"
    return downloads if downloads.is_dir() else Path.home()


class _JsonFile:
    """Archivo JSON con carga tolerante a errores y guardado atómico."""

    def __init__(self, path: Path, default: Any) -> None:
        self.path = path
        self._default = default
        self.data = self._load()

    def _load(self) -> Any:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except (OSError, ValueError):
            return json.loads(json.dumps(self._default))
        if isinstance(self._default, dict) and isinstance(loaded, dict):
            merged = json.loads(json.dumps(self._default))
            merged.update(loaded)
            return merged
        return loaded if isinstance(loaded, type(self._default)) else json.loads(
            json.dumps(self._default)
        )

    def save(self) -> None:
        tmp = self.path.with_name(self.path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump(self.data, handle, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass


class Settings(QObject):
    """Preferencias del usuario (lectura/escritura con guardado inmediato)."""

    changed = Signal(str, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._file = _JsonFile(config_dir() / "settings.json", DEFAULT_SETTINGS)

    def get(self, key: str, default: Any = None) -> Any:
        return self._file.data.get(key, DEFAULT_SETTINGS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        if self._file.data.get(key) == value:
            return
        self._file.data[key] = value
        self._file.save()
        self.changed.emit(key, value)

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self.set(key, value)

    def reset(self) -> None:
        self._file.data = json.loads(json.dumps(DEFAULT_SETTINGS))
        self._file.save()

    @property
    def search_template(self) -> str:
        engine = self.get("search_engine", "duckduckgo")
        return SEARCH_ENGINES.get(engine, SEARCH_ENGINES["duckduckgo"])[1]

    @property
    def download_path(self) -> Path:
        configured = self.get("download_dir") or ""
        if configured:
            path = Path(os.path.expanduser(configured))
            if path.is_dir():
                return path
        return default_download_dir()


class History(QObject):
    """Historial de navegación (más reciente primero)."""

    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._file = _JsonFile(config_dir() / "history.json", [])
        self._entries: list[dict[str, Any]] = self._file.data

    def add(self, title: str, url: str) -> None:
        if not url or url.startswith(("about:", "file:", "data:")):
            return
        title = (title or "").strip() or url

        # Si ya existía, se mueve al principio y se actualiza.
        existing = next((item for item in self._entries if item.get("url") == url), None)
        if existing:
            existing["title"] = title
            existing["visited"] = time.time()
            existing["visits"] = int(existing.get("visits", 1)) + 1
            self._entries.remove(existing)
            self._entries.insert(0, existing)
        else:
            self._entries.insert(
                0,
                {"title": title, "url": url, "visited": time.time(), "visits": 1},
            )

        del self._entries[HISTORY_LIMIT:]
        self._file.data = self._entries
        self._file.save()
        self.changed.emit()

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def search(self, query: str) -> list[dict[str, Any]]:
        query = (query or "").strip().lower()
        if not query:
            return list(self._entries)
        return [
            item
            for item in self._entries
            if query in str(item.get("title", "")).lower()
            or query in str(item.get("url", "")).lower()
        ]

    def completions(self, query: str, limit: int = 8) -> list[str]:
        query = (query or "").strip().lower()
        if not query:
            return []
        matches: list[str] = []
        for item in self._entries:
            url = str(item.get("url", ""))
            if query in url.lower() and url not in matches:
                matches.append(url)
            if len(matches) >= limit:
                break
        return matches

    def remove(self, url: str) -> None:
        self._entries = [item for item in self._entries if item.get("url") != url]
        self._file.data = self._entries
        self._file.save()
        self.changed.emit()

    def clear(self) -> None:
        self._entries = []
        self._file.data = self._entries
        self._file.save()
        self.changed.emit()


class Bookmarks(QObject):
    """Marcadores: lista plana de {title, url, added}.

    Las URLs se comparan por su forma canónica: «https://x.com» y
    «https://x.com/» son el mismo sitio y no deben duplicarse, y la estrella
    de la barra se mantiene aunque la página redirija la barra final.
    """

    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._file = _JsonFile(config_dir() / "bookmarks.json", [])
        self._items: list[dict[str, Any]] = self._file.data
        # Limpia duplicados heredados (mismo sitio con/without barra final).
        if self._dedupe():
            self._persist()

    def items(self) -> list[dict[str, Any]]:
        return list(self._items)

    def _dedupe(self) -> bool:
        seen: set[str] = set()
        kept: list[dict[str, Any]] = []
        changed = False
        for item in self._items:
            key = canonical_url(str(item.get("url", "")))
            if key in seen:
                changed = True
                continue
            seen.add(key)
            kept.append(item)
        if changed:
            self._items = kept
        return changed

    def contains(self, url: str) -> bool:
        key = canonical_url(url)
        return any(canonical_url(str(item.get("url", ""))) == key for item in self._items)

    def add(self, title: str, url: str) -> bool:
        if not url or self.contains(url):
            return False
        self._items.append(
            {
                "title": (title or "").strip() or url,
                "url": url,
                "added": time.time(),
            }
        )
        self._persist()
        return True

    def remove(self, url: str) -> bool:
        key = canonical_url(url)
        before = len(self._items)
        self._items = [
            item
            for item in self._items
            if canonical_url(str(item.get("url", ""))) != key
        ]
        if len(self._items) == before:
            return False
        self._persist()
        return True

    def rename(self, url: str, title: str) -> None:
        key = canonical_url(url)
        for item in self._items:
            if canonical_url(str(item.get("url", ""))) == key:
                item["title"] = (title or "").strip() or str(item.get("url", ""))
                self._persist()
                return

    def toggle(self, title: str, url: str) -> bool:
        """Añade el marcador si falta; lo quita si ya existe. Devuelve si quedó guardado."""
        if self.contains(url):
            self.remove(url)
            return False
        return self.add(title, url)

    def _persist(self) -> None:
        self._file.data = self._items
        self._file.save()
        self.changed.emit()


class Shortcuts(QObject):
    """Accesos rápidos de la nueva pestaña: lista ordenada {title, url, favicon?}."""

    changed = Signal()

    DEFAULT_SHORTCUTS: list[dict[str, Any]] = [
        {"title": "YouTube", "url": "https://www.youtube.com/"},
        {"title": "Wikipedia", "url": "https://es.wikipedia.org/"},
        {"title": "GitHub", "url": "https://github.com/"},
        {"title": "Gmail", "url": "https://mail.google.com/"},
        {"title": "Google Maps", "url": "https://www.google.com/maps"},
        {"title": "DuckDuckGo", "url": "https://duckduckgo.com/"},
    ]

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._file = _JsonFile(config_dir() / "shortcuts.json", [])
        self._items: list[dict[str, Any]] = self._file.data
        if not self._items:
            self._items = [dict(i) for i in self.DEFAULT_SHORTCUTS]
            self._persist()

    def items(self) -> list[dict[str, Any]]:
        return list(self._items)

    def add(self, title: str, url: str) -> bool:
        url = (url or "").strip()
        if not url:
            return False
        title = (title or "").strip() or url
        if any(i.get("url") == url for i in self._items):
            return False
        self._items.append({"title": title, "url": url})
        self._persist()
        return True

    def remove(self, url: str) -> bool:
        before = len(self._items)
        self._items = [i for i in self._items if i.get("url") != url]
        changed = len(self._items) != before
        if changed:
            self._persist()
        return changed

    def reorder(self, urls: list[str]) -> None:
        order = {u: idx for idx, u in enumerate(urls)}
        self._items.sort(key=lambda x: order.get(x.get("url", ""), 9999))
        self._persist()

    def reset_defaults(self) -> None:
        self._items = [dict(i) for i in self.DEFAULT_SHORTCUTS]
        self._persist()

    def _persist(self) -> None:
        self._file.data = self._items
        self._file.save()
        self.changed.emit()


class Session(QObject):
    """Estado de la ventana para poder restaurar la sesión."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._file = _JsonFile(
            data_dir() / "session.json",
            {"tabs": [], "active": 0, "geometry": None, "maximized": False},
        )

    @property
    def data(self) -> dict[str, Any]:
        return self._file.data

    def save(
        self,
        tabs: list[dict[str, Any]],
        active: int,
        geometry: bytes | None,
        maximized: bool,
    ) -> None:
        self._file.data = {
            "tabs": tabs,
            "active": active,
            "geometry": geometry.decode("latin-1") if geometry else None,
            "maximized": maximized,
        }
        self._file.save()

    def geometry(self) -> bytes | None:
        raw = self._file.data.get("geometry")
        return raw.encode("latin-1") if raw else None
