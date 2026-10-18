"""Vistas web: QWebEngineView/QWebEnginePage personalizados.

Qt WebEngine usa el motor Chromium, así que estas vistas renderizan igual que
Chrome. Aquí solo añadimos el pegamento: pestañas nuevas, permisos, errores de
certificado y la página de nueva pestaña.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QUrl, Signal
from PySide6.QtWebEngineCore import (
    QWebEngineCertificateError,
    QWebEnginePage,
    QWebEngineProfile,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

#: Callable que crea una pestaña nueva y devuelve la página que Chromium debe usar.
NewTabHandler = Callable[["WebPage", int], QWebEnginePage | None]


class WebPage(QWebEnginePage):
    """Página web con integración con la ventana del navegador."""

    def __init__(
        self,
        profile: QWebEngineProfile,
        window=None,
        parent=None,
    ) -> None:
        super().__init__(profile, parent or window)
        self.window_ref = window
        self._new_tab_handler: NewTabHandler | None = None
        self._debug_console = False

    # -- integración con pestañas -------------------------------------------
    def set_new_tab_handler(self, handler: NewTabHandler | None) -> None:
        self._new_tab_handler = handler

    def createWindow(self, window_type) -> QWebEnginePage | None:  # noqa: N802 (API de Qt)
        """Chromium pide una ventana nueva (target=_blank, window.open…)."""
        if self._new_tab_handler is None:
            return None
        return self._new_tab_handler(self, window_type)

    # -- diagnóstico --------------------------------------------------------
    def set_debug_console(self, enabled: bool) -> None:
        self._debug_console = bool(enabled)

    def javaScriptConsoleMessage(  # noqa: N802 (API de Qt)
        self, level, message: str, lineNumber: int, sourceID: str
    ) -> None:
        if self._debug_console:
            print(f"[JS {level}] {sourceID}:{lineNumber} {message}")

    def certificateError(self, error: QWebEngineCertificateError) -> bool:  # noqa: N802
        """Acepta certificados inválidos solo si el usuario lo habilitó."""
        window = self.window_ref
        ignore = bool(getattr(window, "ignore_certificate_errors", False))
        if ignore:
            error.acceptCertificate()
            return True
        if window is not None and hasattr(window, "notify_certificate_error"):
            window.notify_certificate_error(error)
        error.rejectCertificate()
        return True  # ya gestionamos el error aquí


class WebView(QWebEngineView):
    """Vista web con estado propio de pestaña (zoom, página de inicio, etc.)."""

    #: (mensaje, segundos de visibilidad) para la barra de estado.
    status_hint = Signal(str, int)

    def __init__(self, profile: QWebEngineProfile, window=None, parent=None) -> None:
        super().__init__(parent or window)
        self.window_ref = window
        self.is_new_tab_page = False
        self.zoom = 1.0
        # Navegación en curso: isLoading() de la página no es síncrono tras
        # setUrl(), así que lo seguimos nosotros para poder diferir acciones
        # (p. ej. guardar un marcador) hasta tener la URL y el título finales.
        self.nav_pending = False

        page = WebPage(profile, window=window, parent=self)
        self.setPage(page)

        page.linkHovered.connect(self._on_link_hovered)
        page.loadStarted.connect(self._on_nav_started)
        page.loadFinished.connect(self._on_nav_finished)

    def _on_nav_started(self) -> None:
        self.nav_pending = True

    def _on_nav_finished(self, _ok: bool) -> None:
        self.nav_pending = False

    @property
    def is_loading(self) -> bool:
        """True si hay una navegación en curso (cualquier motivo)."""
        return self.nav_pending or self.web_page.isLoading()

    # -- utilidades ---------------------------------------------------------
    @property
    def web_page(self) -> WebPage:
        return self.page()  # type: ignore[return-value]

    def url_string(self) -> str:
        return self.url().toString()

    def load_input(self, url: str) -> None:
        """Carga una URL ya normalizada, tratando la página de nueva pestaña."""
        if not url:
            return
        self.is_new_tab_page = False
        self.nav_pending = True  # loadStarted puede llegar tarde: lo marcamos ya.
        self.setUrl(QUrl(url))

    def load_html_page(self, html: str, base: str = "about:blank") -> None:
        self.is_new_tab_page = True
        self.setHtml(html, QUrl(base))

    def set_zoom(self, factor: float) -> None:
        self.zoom = max(0.25, min(5.0, factor))
        self.setZoomFactor(self.zoom)

    def _on_link_hovered(self, url: str) -> None:
        self.status_hint.emit(url or "", 0)
