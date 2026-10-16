"""Gestión de descargas: seguimiento, barra inferior y diálogo."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from .utils import color_for, human_size, initial_letter, truncate

_STATE_TEXT = {
    QWebEngineDownloadRequest.DownloadState.DownloadRequested: "En cola",
    QWebEngineDownloadRequest.DownloadState.DownloadInProgress: "Descargando",
    QWebEngineDownloadRequest.DownloadState.DownloadCompleted: "Completada",
    QWebEngineDownloadRequest.DownloadState.DownloadCancelled: "Cancelada",
    QWebEngineDownloadRequest.DownloadState.DownloadInterrupted: "Interrumpida",
}


def _unique_path(directory: Path, filename: str) -> Path:
    """Evita sobrescribir: archivo.txt → archivo (1).txt"""
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    for index in range(1, 1000):
        alternative = directory / f"{stem} ({index}){suffix}"
        if not alternative.exists():
            return alternative
    return candidate


class Download(QObject):
    """Descarga individual con su estado y utilidades de apertura."""

    updated = Signal()
    finished = Signal()

    def __init__(self, request: QWebEngineDownloadRequest, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.request = request
        self.path = Path(request.downloadDirectory()) / request.downloadFileName()
        self._last_state = request.state()

        request.receivedBytesChanged.connect(self._changed)
        request.totalBytesChanged.connect(self._changed)
        request.isFinishedChanged.connect(self._changed)
        request.stateChanged.connect(self._on_state_changed)

    # -- estado -------------------------------------------------------------
    @property
    def name(self) -> str:
        return self.request.downloadFileName() or "descarga"

    @property
    def url(self) -> str:
        return self.request.url().toString()

    @property
    def total(self) -> int:
        return int(self.request.totalBytes())

    @property
    def received(self) -> int:
        return int(self.request.receivedBytes())

    @property
    def state(self):
        return self.request.state()

    @property
    def is_finished(self) -> bool:
        return self.request.isFinished()

    @property
    def is_active(self) -> bool:
        return self.state in (
            QWebEngineDownloadRequest.DownloadState.DownloadRequested,
            QWebEngineDownloadRequest.DownloadState.DownloadInProgress,
        )

    @property
    def is_paused(self) -> bool:
        return self.request.isPaused()

    @property
    def progress(self) -> int:
        if self.total <= 0:
            return 0 if self.is_active else 100
        return max(0, min(100, int(self.received * 100 / self.total)))

    @property
    def state_text(self) -> str:
        text = _STATE_TEXT.get(self.state, "Desconocido")
        if self.state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            reason = self.request.interruptReasonString()
            text = f"{text}: {reason}" if reason else text
        elif self.state == QWebEngineDownloadRequest.DownloadState.DownloadInProgress and self.is_paused:
            text = "En pausa"
        return text

    @property
    def size_text(self) -> str:
        if self.total > 0:
            return f"{human_size(self.received)} de {human_size(self.total)}"
        return human_size(self.received)

    # -- acciones -----------------------------------------------------------
    def pause_or_resume(self) -> None:
        if self.request.isPaused():
            self.request.resume()
        elif self.is_active:
            self.request.pause()
        self._changed()

    def cancel(self) -> None:
        if self.is_active:
            self.request.cancel()
        self._changed()

    def open_file(self) -> None:
        if self.path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.path)))
        else:
            QMessageBox.warning(
                None, "Descarga", f"El archivo ya no existe:\n{self.path}"
            )

    def open_folder(self) -> None:
        folder = self.path if self.path.is_dir() else self.path.parent
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    # -- señales ------------------------------------------------------------
    def _changed(self) -> None:
        self.updated.emit()

    def _on_state_changed(self, state) -> None:
        self.updated.emit()
        if state in (
            QWebEngineDownloadRequest.DownloadState.DownloadCompleted,
            QWebEngineDownloadRequest.DownloadState.DownloadCancelled,
            QWebEngineDownloadRequest.DownloadState.DownloadInterrupted,
        ) and self.is_finished:
            self.finished.emit()


class DownloadsManager(QObject):
    """Recibe las descargas del perfil y las mantiene accesibles."""

    started = Signal(object)   # Download
    updated = Signal(object)   # Download
    finished = Signal(object)  # Download

    def __init__(self, settings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._downloads: list[Download] = []

    def attach(self, profile: QWebEngineProfile) -> None:
        profile.downloadRequested.connect(self._on_request)

    def downloads(self) -> list[Download]:
        return list(reversed(self._downloads))

    def active_count(self) -> int:
        return sum(1 for item in self._downloads if item.is_active)

    def clear_finished(self) -> None:
        self._downloads = [item for item in self._downloads if not item.is_finished]
        self.updated.emit(None)

    # -- recepción ----------------------------------------------------------
    def _on_request(self, request: QWebEngineDownloadRequest) -> None:
        directory = self.settings.download_path

        if self.settings.get("ask_download_dir", False):
            chosen, _ = QFileDialog.getSaveFileName(
                None,
                "Guardar archivo",
                str(directory / (request.suggestedFileName() or request.downloadFileName())),
            )
            if not chosen:
                request.cancel()
                return
            target = Path(chosen)
            directory, filename = target.parent, target.name
        else:
            filename = request.suggestedFileName() or request.downloadFileName() or "descarga"
            directory = Path(str(directory))
            directory.mkdir(parents=True, exist_ok=True)
            filename = _unique_path(directory, filename).name

        request.setDownloadDirectory(str(directory))
        request.setDownloadFileName(filename)
        request.accept()

        download = Download(request, self)
        download.updated.connect(lambda d=download: self.updated.emit(d))
        download.finished.connect(lambda d=download: self.finished.emit(d))
        self._downloads.append(download)
        self.started.emit(download)
        self.updated.emit(download)


class DownloadRow(QFrame):
    """Fila reutilizable que representa una descarga en la interfaz."""

    def __init__(self, download: Download, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.download = download

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self.icon = QLabel(initial_letter(download.name))
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setFixedSize(30, 30)
        self.icon.setStyleSheet(
            f"background:{color_for(download.name)}; color:#202124;"
            "border-radius:15px; font-weight:600;"
        )
        layout.addWidget(self.icon)

        middle = QVBoxLayout()
        middle.setSpacing(4)
        self.name_label = QLabel(truncate(download.name, 64))
        self.name_label.setToolTip(download.url)
        middle.addWidget(self.name_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        middle.addWidget(self.progress)
        layout.addLayout(middle, 1)

        self.status = QLabel()
        self.status.setObjectName("MutedHint")
        self.status.setMinimumWidth(170)
        layout.addWidget(self.status)

        self.toggle = QToolButton()
        self.toggle.setText("Pausar")
        self.toggle.clicked.connect(download.pause_or_resume)
        layout.addWidget(self.toggle)

        self.open_button = QToolButton()
        self.open_button.setText("Abrir")
        self.open_button.clicked.connect(download.open_file)
        layout.addWidget(self.open_button)

        self.folder_button = QToolButton()
        self.folder_button.setText("Carpeta")
        self.folder_button.clicked.connect(download.open_folder)
        layout.addWidget(self.folder_button)

        download.updated.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        download = self.download
        self.progress.setValue(download.progress)
        if download.total <= 0 and download.is_active:
            self.progress.setRange(0, 0)  # indeterminado
        else:
            self.progress.setRange(0, 100)
        self.status.setText(f"{download.state_text} · {download.size_text}")
        self.toggle.setVisible(download.is_active)
        self.toggle.setText("Reanudar" if download.is_paused else "Pausar")
        self.open_button.setEnabled(download.path.exists() and not download.is_active)
        self.folder_button.setEnabled(download.path.exists())
        self.name_label.setText(truncate(download.name, 64))


class DownloadsDialog(QDialog):
    """Ventana con todas las descargas de la sesión."""

    def __init__(self, manager: DownloadsManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.rows: dict[int, DownloadRow] = {}

        self.setWindowTitle("Descargas")
        self.resize(760, 460)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        title = QLabel("Descargas")
        title.setObjectName("PanelTitle")
        outer.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll, 1)

        self.empty_hint = QLabel("No hay descargas en esta sesión.")
        self.empty_hint.setObjectName("MutedHint")
        outer.addWidget(self.empty_hint)

        buttons = QHBoxLayout()
        clear = QPushButton("Limpiar completadas")
        clear.clicked.connect(self._clear)
        buttons.addWidget(clear)
        buttons.addStretch(1)
        close = QPushButton("Cerrar")
        close.setDefault(True)
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        outer.addLayout(buttons)

        manager.updated.connect(self._on_manager_update)
        self.refresh()

    def _clear(self) -> None:
        self.manager.clear_finished()
        self.refresh()

    def _on_manager_update(self, _download) -> None:
        if self.isVisible():
            self.refresh()

    def refresh(self) -> None:
        downloads = self.manager.downloads()
        wanted = {id(item): item for item in downloads}

        for key in list(self.rows):
            if key not in wanted:
                row = self.rows.pop(key)
                row.setVisible(False)
                row.setParent(None)
                row.deleteLater()

        for index, download in enumerate(downloads):
            row = self.rows.get(id(download))
            if row is None:
                row = DownloadRow(download, self.container)
                self.rows[id(download)] = row
            row.setVisible(True)
            self.list_layout.removeWidget(row)
            self.list_layout.insertWidget(index, row)

        self.empty_hint.setVisible(not downloads)
