"""Persistencia del navegador: ajustes, historial, marcadores y sesión.

Todo se guarda como JSON en el directorio de configuración del usuario:
%APPDATA% y %LOCALAPPDATA% en Windows, directorios XDG en Linux.
"""

from __future__ import annotations

import json
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

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

    def __init__(self, path: Path, default: Any, *, indent: int | None = None) -> None:
        self.path = path
        self._default = default
        self._indent = indent
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
        # Los archivos grandes (historial, sesión) se guardan compactos: el
        # sangrado de 2 espacios multiplicaba por ~1,6 el tamaño y el tiempo de
        # escritura en cada navegación. settings.json sí queda legible.
        kwargs: dict[str, Any] = {"ensure_ascii": False}
        if self._indent is None:
            kwargs["separators"] = (",", ":")
        else:
            kwargs["indent"] = self._indent
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump(self.data, handle, **kwargs)
            os.replace(tmp, self.path)
        except OSError:
            pass


class Settings(QObject):
    """Preferencias del usuario (lectura/escritura con guardado inmediato)."""

    changed = Signal(str, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._file = _JsonFile(config_dir() / "settings.json", DEFAULT_SETTINGS, indent=2)

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
    """Historial de navegación (más reciente primero).

    El guardado en disco se difiere: navegar no debe reescribir todo el JSON
    en cada carga. `flush()` fuerza la escritura (al cerrar la ventana y al
    salir de la aplicación).
    """

    changed = Signal()

    # Se guarda tras 3 s sin navegar (o cada 100 cambios, para no perder
    # demasiado si el navegador se cierra de golpe). Con 8.000 entradas,
    # escribir el JSON bloquea ~120 ms: mejor una vez en reposo que en cada
    # carga de página.
    SAVE_DELAY_MS = 3000
    MAX_PENDING_SAVES = 100

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._file = _JsonFile(config_dir() / "history.json", [])
        # OrderedDict: mover una URL al principio y expulsar la más antigua
        # son O(1), en vez de recorrer y reordenar miles de entradas.
        self._entries: OrderedDict[str, dict[str, Any]] = OrderedDict()
        for item in self._file.data:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", ""))
            if url and url not in self._entries:
                self._entries[url] = item
        self._dirty = False
        self._pending = 0
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(self.SAVE_DELAY_MS)
        self._save_timer.timeout.connect(self.flush)

    def _schedule_save(self) -> None:
        self._dirty = True
        self._pending += 1
        if self._pending >= self.MAX_PENDING_SAVES:
            self.flush()
        else:
            # Reinicia la cuenta atrás: si el usuario sigue navegando, no se
            # escribe hasta que lleve 3 s parado.
            self._save_timer.start()

    def flush(self) -> None:
        """Escribe ahora los cambios pendientes (si los hay)."""
        if self._save_timer.isActive():
            self._save_timer.stop()
        self._pending = 0
        if not self._dirty:
            return
        self._file.data = list(self._entries.values())
        self._file.save()
        self._dirty = False

    def add(self, title: str, url: str) -> None:
        if not url or url.startswith(("about:", "file:", "data:")):
            return
        title = (title or "").strip() or url

        now = time.time()
        existing = self._entries.get(url)
        if existing is not None:
            existing["title"] = title
            existing["visited"] = now
            existing["visits"] = int(existing.get("visits", 1)) + 1
            self._entries.move_to_end(url, last=False)
        else:
            self._entries[url] = {
                "title": title,
                "url": url,
                "visited": now,
                "visits": 1,
            }
            self._entries.move_to_end(url, last=False)

        while len(self._entries) > HISTORY_LIMIT:
            self._entries.popitem(last=True)

        self._schedule_save()
        self.changed.emit()

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries.values())

    def search(self, query: str) -> list[dict[str, Any]]:
        query = (query or "").strip().lower()
        if not query:
            return list(self._entries.values())
        return [
            item
            for item in self._entries.values()
            if query in str(item.get("title", "")).lower()
            or query in str(item.get("url", "")).lower()
        ]

    def completions(self, query: str, limit: int = 8) -> list[str]:
        query = (query or "").strip().lower()
        if not query:
            return []
        matches: list[str] = []
        seen: set[str] = set()
        for item in self._entries.values():
            url = str(item.get("url", ""))
            if url not in seen and query in url.lower():
                seen.add(url)
                matches.append(url)
                if len(matches) >= limit:
                    break
        return matches

    def remove(self, url: str) -> None:
        if self._entries.pop(url, None) is None:
            return
        self._schedule_save()
        self.changed.emit()

    def clear(self) -> None:
        self._entries.clear()
        self._dirty = True
        # Borrar datos es una acción explícita: se escribe ya, sin esperar.
        self.flush()
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
        # Índice de URLs canónicas: `contains()` se llama en cada navegación
        # (para la estrella) y recorrer la lista entera era O(n).
        self._keys: set[str] = set()
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
        self._keys = seen
        return changed

    def contains(self, url: str) -> bool:
        return bool(url) and canonical_url(url) in self._keys

    def add(self, title: str, url: str) -> bool:
        key = canonical_url(url)
        if not url or key in self._keys:
            return False
        self._items.append(
            {
                "title": (title or "").strip() or url,
                "url": url,
                "added": time.time(),
            }
        )
        self._keys.add(key)
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
        self._keys.discard(key)
        self._persist()
        return True

    def rename(self, url: str, title: str) -> None:
        key = canonical_url(url)
        if key not in self._keys:
            return
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
