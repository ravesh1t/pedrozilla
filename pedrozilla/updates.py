"""Comprobación de actualizaciones contra las releases de GitHub.

La consulta es deliberadamente pequeña: una petición a la API pública, sin
telemetría y sin descargar nada. El navegador solo avisa de que hay una versión
nueva y abre la página de la release para que el usuario decida.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

GITHUB_REPO = "ravesh1t/pedrozilla"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
LATEST_RELEASE_URL = os.environ.get(
    "PEDROZILLA_UPDATE_URL",
    f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
)


def parse_version(value: str) -> tuple[int, ...]:
    """Extrae la parte numérica de un tag (`v1.2.3` -> `(1, 2, 3)`)."""
    match = re.search(r"(\d+(?:\.\d+)*)", value or "")
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(latest: str, current: str) -> bool:
    """Compara versiones numéricas rellenando con ceros a la derecha."""
    latest_parts = parse_version(latest)
    current_parts = parse_version(current)
    if not latest_parts or not current_parts:
        return False
    size = max(len(latest_parts), len(current_parts))
    latest_parts += (0,) * (size - len(latest_parts))
    current_parts += (0,) * (size - len(current_parts))
    return latest_parts > current_parts


class UpdateChecker(QObject):
    """Consulta asíncrona de la última release publicada en GitHub."""

    update_available = Signal(str, str, str)  # versión, página, notas
    no_update = Signal()
    failed = Signal(str)

    def __init__(self, current_version: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self._manager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None

    def check(self) -> None:
        if self._reply is not None:
            return
        request = QNetworkRequest(QUrl(LATEST_RELEASE_URL))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(
            b"User-Agent",
            f"Pedrozilla/{self.current_version}".encode("ascii", "replace"),
        )
        try:
            request.setAttribute(
                QNetworkRequest.Attribute.RedirectPolicyAttribute,
                QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
            )
            request.setTransferTimeout(15000)
        except (AttributeError, TypeError):
            # Qt antiguo: se mantiene la petición sin timeout explícito.
            pass

        self._reply = self._manager.get(request)
        self._reply.finished.connect(self._on_finished)

    def _on_finished(self) -> None:
        reply = self._reply
        self._reply = None
        if reply is None:
            return

        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
                message = reply.errorString()
                if status:
                    message = f"HTTP {status}: {message}"
                self.failed.emit(message)
                return

            raw = bytes(reply.readAll()).decode("utf-8", "replace")
            payload: Any = json.loads(raw)
            if not isinstance(payload, dict):
                self.failed.emit("La respuesta de GitHub no es válida.")
                return

            tag = str(payload.get("tag_name") or payload.get("name") or "").strip()
            page = str(payload.get("html_url") or RELEASES_URL).strip()
            notes = str(payload.get("body") or "").strip()
            if not tag:
                self.failed.emit("La release no incluye un número de versión.")
            elif is_newer(tag, self.current_version):
                self.update_available.emit(tag, page or RELEASES_URL, notes)
            else:
                self.no_update.emit()
        except (OSError, ValueError, TypeError) as exc:
            self.failed.emit(str(exc))
        finally:
            reply.deleteLater()
