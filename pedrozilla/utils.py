"""Utilidades compartidas: parseo de la barra de direcciones y formateo."""

from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

# Esquemas web que aceptamos tal cual desde la barra de direcciones.
WEB_SCHEMES = {
    "http", "https", "file", "ftp", "ftps", "about", "view-source", "ws", "wss",
}
# Otros esquemas legítimos que Chromium o el sistema pueden manejar.
EXOTIC_SCHEMES = {
    "mailto", "magnet", "irc", "ircs", "sms", "tel", "spotify", "steam", "callto",
    "webcal", "feed", "chrome", "chromium", "edge", "chrome-extension", "moz-extension",
}
# Esquemas que nunca se ejecutan desde la omnibox (se tratan como búsqueda).
BLOCKED_SCHEMES = {"javascript", "data", "blob", "vbscript"}

_SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):")
_IP_RE = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?")
_LOCAL_RE = re.compile(r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(?::\d+)?", re.IGNORECASE)
_DOMAIN_RE = re.compile(r"[^\s/@:]+(?:\.[^\s/@:]+)*\.[a-zA-Z]{2,}(?::\d+)?")


def _host_like(text: str) -> bool:
    """¿El texto es un host navegable (localhost, IP o dominio)? """
    host = text.split("/")[0].split("?")[0].split("#")[0]
    if not host or " " in host:
        return False
    if _LOCAL_RE.fullmatch(host) or _IP_RE.fullmatch(host):
        return True
    return _DOMAIN_RE.fullmatch(host) is not None


def _has_explicit_scheme(text: str) -> bool:
    """¿Trae un esquema escrito por el usuario (http://, mailto:, …)?"""
    match = _SCHEME_RE.match(text)
    if not match:
        return False
    scheme = match.group(1).lower()
    if scheme in WEB_SCHEMES or scheme in EXOTIC_SCHEMES:
        # "localhost:8080" parece un esquema, pero es un host con puerto.
        rest = text[match.end():]
        if scheme not in WEB_SCHEMES and rest[:1].isdigit():
            return False
        return True
    return text.startswith(f"{match.group(1)}://")


def looks_like_url(text: str) -> bool:
    """Heurística tipo omnibox: ¿el texto parece una dirección y no una búsqueda?"""
    text = (text or "").strip()
    if not text or " " in text:
        return False

    match = _SCHEME_RE.match(text)
    if match and match.group(1).lower() in BLOCKED_SCHEMES:
        return False
    if _has_explicit_scheme(text):
        return True
    return _host_like(text)


def normalize_input(text: str, search_template: str) -> str:
    """Convierte lo escrito en la omnibox en una URL navegable."""
    text = (text or "").strip()
    if not text:
        return ""
    if looks_like_url(text):
        if _has_explicit_scheme(text):
            return text
        return "http://" + text
    return search_template.replace("{query}", quote(text, safe=""))


def host_of(url: str) -> str:
    try:
        return urlsplit(url).hostname or ""
    except ValueError:
        return ""


def is_web_url(url: str) -> bool:
    try:
        return urlsplit(url).scheme in ("http", "https")
    except ValueError:
        return False


def display_url(url: str, max_len: int = 72) -> str:
    """URL compacta para la barra de estado (sin esquema ni www)."""
    if not url:
        return ""
    pretty = re.sub(r"^https?://(?:www\.)?", "", url)
    if len(pretty) > max_len:
        pretty = pretty[: max_len - 1] + "…"
    return pretty


def truncate(text: str, limit: int = 40) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def human_size(num_bytes: float | int | None) -> str:
    if not num_bytes or num_bytes < 0:
        return "0 B"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def decorate_user_agent(user_agent: str) -> str:
    """Elimina el token QtWebEngine para que los sitios no sirvan páginas degradadas."""
    return re.sub(r"\s*QtWebEngine/\S+", "", user_agent or "").strip()


def initial_letter(text: str) -> str:
    for char in text or "":
        if char.isalnum():
            return char.upper()
    return "?"


# Paleta estable por sitio para los iconos generados (favicon de reserva).
_ICON_COLORS = (
    "#e0533d", "#c9432f", "#e08a1e", "#d9a400", "#4c9a2a",
    "#2f9e7a", "#2b8fd4", "#4a6fd4", "#7a5cd4", "#b04fd4",
)


def color_for(text: str) -> str:
    total = sum(ord(char) for char in (text or "?"))
    return _ICON_COLORS[total % len(_ICON_COLORS)]
