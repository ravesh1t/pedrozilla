"""Diálogos: historial, marcadores, ajustes y acerca de."""

from __future__ import annotations

import time
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .storage import APP_NAME, DEFAULT_SETTINGS, SEARCH_ENGINES
from .utils import truncate

Navigator = Callable[[str, bool], None]  # (url, en_pestaña_nueva)


def _stamp(timestamp: float | None) -> str:
    if not timestamp:
        return ""
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(float(timestamp)))


class _TableDialog(QDialog):
    """Base para listados con búsqueda y acciones."""

    columns: tuple[str, ...] = ()
    empty_text = "Sin resultados"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.navigate: Navigator | None = None

        self.setMinimumSize(820, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("PanelTitle")
        layout.addWidget(self.title_label)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels(list(self.columns))
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.itemDoubleClicked.connect(lambda _item: self.open_current(False))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for index in range(1, len(self.columns)):
            header.setSectionResizeMode(index, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.hint = QLabel(self.empty_text)
        self.hint.setObjectName("MutedHint")
        layout.addWidget(self.hint)

        actions = QHBoxLayout()
        self.extra_actions: QHBoxLayout = actions
        actions.addStretch(1)
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.accept)
        actions.addWidget(self.close_button)
        layout.addLayout(actions)

    # -- API para las subclases --------------------------------------------
    def current_row(self) -> int:
        return self.table.currentRow()

    def current_url(self) -> str:
        row = self.current_row()
        if row < 0:
            return ""
        item = self.table.item(row, len(self.columns) - 1)
        return item.data(Qt.ItemDataRole.UserRole) if item else ""

    def set_rows(self, rows: list[tuple[list[str], str]]) -> None:
        """rows: [([columnas...], url), ...]"""
        self.table.setRowCount(0)
        for values, url in rows:
            index = self.table.rowCount()
            self.table.insertRow(index)
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                item.setData(Qt.ItemDataRole.UserRole, url)
                self.table.setItem(index, column, item)
        self.hint.setVisible(bool(rows) is False)

    def open_current(self, new_tab: bool = False) -> None:
        url = self.current_url()
        if url and self.navigate is not None:
            self.navigate(url, new_tab)


class HistoryDialog(_TableDialog):
    columns = ("Título", "Dirección", "Visitas", "Última visita")

    def __init__(self, history, navigate: Navigator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.history = history
        self.navigate = navigate
        self.setWindowTitle("Historial")
        self.title_label.setText("Historial de navegación")
        self.search.setPlaceholderText("Buscar en el historial…")
        self.empty_text = "No hay entradas en el historial."

        open_tab = QPushButton("Abrir en pestaña nueva")
        open_tab.clicked.connect(lambda: self.open_current(True))
        self.extra_actions.insertWidget(0, open_tab)
        open_button = QPushButton("Abrir")
        open_button.clicked.connect(lambda: self.open_current(False))
        self.extra_actions.insertWidget(1, open_button)
        delete = QPushButton("Eliminar")
        delete.clicked.connect(self._delete_current)
        clear = QPushButton("Borrar todo")
        clear.clicked.connect(self._clear)
        self.extra_actions.insertWidget(2, delete)
        self.extra_actions.insertWidget(3, clear)

        self.refresh()

    def refresh(self) -> None:
        entries = self.history.search(self.search.text())
        rows = []
        for item in entries:
            url = str(item.get("url", ""))
            rows.append(
                (
                    [
                        truncate(str(item.get("title", "")) or url, 70),
                        truncate(url, 80),
                        str(item.get("visits", 1)),
                        _stamp(item.get("visited")),
                    ],
                    url,
                )
            )
        self.set_rows(rows)

    def _delete_current(self) -> None:
        url = self.current_url()
        if url:
            self.history.remove(url)
            self.refresh()

    def _clear(self) -> None:
        answer = QMessageBox.question(
            self, "Borrar historial", "¿Borrar todo el historial de navegación?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.refresh()


class BookmarksDialog(_TableDialog):
    columns = ("Nombre", "Dirección", "Añadido")

    def __init__(self, bookmarks, navigate: Navigator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.bookmarks = bookmarks
        self.navigate = navigate
        self.setWindowTitle("Marcadores")
        self.title_label.setText("Marcadores")
        self.search.setPlaceholderText("Buscar marcadores…")
        self.empty_text = "Todavía no has guardado marcadores."

        open_tab = QPushButton("Abrir en pestaña nueva")
        open_tab.clicked.connect(lambda: self.open_current(True))
        self.extra_actions.insertWidget(0, open_tab)
        open_button = QPushButton("Abrir")
        open_button.clicked.connect(lambda: self.open_current(False))
        self.extra_actions.insertWidget(1, open_button)
        rename = QPushButton("Renombrar")
        rename.clicked.connect(self._rename)
        remove = QPushButton("Eliminar")
        remove.clicked.connect(self._remove)
        self.extra_actions.insertWidget(2, rename)
        self.extra_actions.insertWidget(3, remove)

        self.refresh()

    def refresh(self) -> None:
        query = self.search.text().strip().lower()
        rows = []
        for item in self.bookmarks.items():
            title = str(item.get("title", ""))
            url = str(item.get("url", ""))
            if query and query not in title.lower() and query not in url.lower():
                continue
            rows.append(
                ([truncate(title or url, 60), truncate(url, 80), _stamp(item.get("added"))], url)
            )
        self.set_rows(rows)

    def _rename(self) -> None:
        row = self.current_row()
        if row < 0:
            return
        url = self.current_url()
        current = self.table.item(row, 0).text()
        new_name, ok = QInputDialog.getText(self, "Renombrar marcador", "Nombre:", text=current)
        if ok and new_name.strip():
            self.bookmarks.rename(url, new_name.strip())
            self.refresh()

    def _remove(self) -> None:
        url = self.current_url()
        if url:
            self.bookmarks.remove(url)
            self.refresh()


class SettingsDialog(QDialog):
    """Preferencias. Se leen con `values()` tras aceptar."""

    def __init__(self, settings, parent: QWidget | None = None, clear_data=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._clear_data = clear_data

        self.setWindowTitle("Ajustes")
        self.resize(620, 460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.setObjectName("DialogTabs")
        tabs.addTab(self._general_tab(), "General")
        tabs.addTab(self._appearance_tab(), "Apariencia")
        tabs.addTab(self._advanced_tab(), "Avanzado")
        layout.addWidget(tabs, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -- pestañas -----------------------------------------------------------
    def _general_tab(self) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)

        form.addWidget(QLabel("Motor de búsqueda de la barra de direcciones"))
        self.engine = QComboBox()
        for key, (label, _template) in SEARCH_ENGINES.items():
            self.engine.addItem(label, key)
        index = self.engine.findData(self.settings.get("search_engine"))
        self.engine.setCurrentIndex(max(0, index))
        form.addWidget(self.engine)

        form.addWidget(QLabel("Página de inicio (vacío = página de nueva pestaña)"))
        self.homepage = QLineEdit(self.settings.get("homepage", ""))
        self.homepage.setPlaceholderText("https://ejemplo.com")
        form.addWidget(self.homepage)

        form.addWidget(QLabel("Al abrir el navegador"))
        self.startup = QComboBox()
        self.startup.addItem("Mostrar la página de nueva pestaña", "newtab")
        self.startup.addItem("Restaurar las pestañas de la última sesión", "restore")
        self.startup.addItem("Abrir la página de inicio", "homepage")
        self.startup.setCurrentIndex(max(0, self.startup.findData(self.settings.get("startup"))))
        form.addWidget(self.startup)

        form.addWidget(QLabel("Carpeta de descargas"))
        row = QHBoxLayout()
        self.download_dir = QLineEdit(self.settings.get("download_dir", ""))
        self.download_dir.setPlaceholderText(str(self.settings.download_path))
        browse = QPushButton("Elegir…")
        browse.clicked.connect(self._pick_folder)
        row.addWidget(self.download_dir, 1)
        row.addWidget(browse)
        form.addLayout(row)

        self.ask_dir = QCheckBox("Preguntar dónde guardar cada archivo")
        self.ask_dir.setChecked(bool(self.settings.get("ask_download_dir")))
        form.addWidget(self.ask_dir)

        form.addStretch(1)
        return page

    def _appearance_tab(self) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)

        form.addWidget(QLabel("Tema de la interfaz"))
        self.theme = QComboBox()
        self.theme.addItem("Oscuro", "dark")
        self.theme.addItem("Claro", "light")
        self.theme.setCurrentIndex(max(0, self.theme.findData(self.settings.get("theme"))))
        form.addWidget(self.theme)

        self.show_bookmarks = QCheckBox("Mostrar la barra de marcadores")
        self.show_bookmarks.setChecked(bool(self.settings.get("show_bookmarks_bar")))
        form.addWidget(self.show_bookmarks)

        form.addWidget(QLabel("Zoom predeterminado de las páginas (%)"))
        self.zoom = QDoubleSpinBox()
        self.zoom.setRange(25, 500)
        self.zoom.setSingleStep(10)
        self.zoom.setDecimals(0)
        self.zoom.setValue(float(self.settings.get("default_zoom", 1.0)) * 100)
        form.addWidget(self.zoom)

        form.addStretch(1)
        return page

    def _advanced_tab(self) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)

        form.addWidget(QLabel("User agent (vacío = el de Chromium)"))
        self.user_agent = QLineEdit(self.settings.get("user_agent", ""))
        self.user_agent.setPlaceholderText("Mozilla/5.0 …")
        form.addWidget(self.user_agent)

        self.javascript = QCheckBox("Permitir JavaScript")
        self.javascript.setChecked(bool(self.settings.get("javascript")))
        form.addWidget(self.javascript)

        self.ignore_certs = QCheckBox("Ignorar errores de certificado (¡inseguro!)")
        self.ignore_certs.setChecked(bool(self.settings.get("ignore_certificate_errors")))
        form.addWidget(self.ignore_certs)

        warning = QLabel(
            "Cambiar el user agent y JavaScript requiere recargar las pestañas abiertas."
        )
        warning.setObjectName("MutedHint")
        warning.setWordWrap(True)
        form.addWidget(warning)

        form.addSpacing(8)
        reset = QPushButton("Restaurar valores por defecto")
        reset.clicked.connect(self._reset_defaults)
        form.addWidget(reset)

        if self._clear_data is not None:
            clear = QPushButton("Borrar datos de navegación (cookies, caché, historial)…")
            clear.clicked.connect(self._clear_data)
            form.addWidget(clear)

        form.addStretch(1)
        return page

    # -- helpers ------------------------------------------------------------
    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Carpeta de descargas", self.download_dir.text() or str(self.settings.download_path)
        )
        if folder:
            self.download_dir.setText(folder)

    def _reset_defaults(self) -> None:
        self.engine.setCurrentIndex(max(0, self.engine.findData(DEFAULT_SETTINGS["search_engine"])))
        self.homepage.setText(DEFAULT_SETTINGS["homepage"])
        self.startup.setCurrentIndex(max(0, self.startup.findData(DEFAULT_SETTINGS["startup"])))
        self.download_dir.setText(DEFAULT_SETTINGS["download_dir"])
        self.ask_dir.setChecked(DEFAULT_SETTINGS["ask_download_dir"])
        self.theme.setCurrentIndex(max(0, self.theme.findData(DEFAULT_SETTINGS["theme"])))
        self.show_bookmarks.setChecked(DEFAULT_SETTINGS["show_bookmarks_bar"])
        self.zoom.setValue(DEFAULT_SETTINGS["default_zoom"] * 100)
        self.user_agent.setText(DEFAULT_SETTINGS["user_agent"])
        self.javascript.setChecked(DEFAULT_SETTINGS["javascript"])
        self.ignore_certs.setChecked(DEFAULT_SETTINGS["ignore_certificate_errors"])

    def values(self) -> dict[str, Any]:
        return {
            "search_engine": self.engine.currentData(),
            "homepage": self.homepage.text().strip(),
            "startup": self.startup.currentData(),
            "download_dir": self.download_dir.text().strip(),
            "ask_download_dir": self.ask_dir.isChecked(),
            "theme": self.theme.currentData(),
            "show_bookmarks_bar": self.show_bookmarks.isChecked(),
            "default_zoom": round(self.zoom.value() / 100, 2),
            "user_agent": self.user_agent.text().strip(),
            "javascript": self.javascript.isChecked(),
            "ignore_certificate_errors": self.ignore_certs.isChecked(),
        }


ABOUT_KEYS = [
    ("Ctrl+T", "Nueva pestaña"),
    ("Ctrl+W", "Cerrar pestaña"),
    ("Ctrl+Shift+N", "Ventana privada (incógnito)"),
    ("Ctrl+Shift+T", "Reabrir la última pestaña cerrada"),
    ("Ctrl+L / Alt+D", "Ir a la barra de direcciones"),
    ("Ctrl+D", "Guardar marcador"),
    ("Ctrl+Shift+B", "Mostrar/ocultar barra de marcadores"),
    ("Ctrl+H", "Historial"),
    ("Ctrl+J", "Descargas"),
    ("Ctrl+R / F5", "Recargar"),
    ("Alt+←/→", "Atrás / adelante"),
    ("Ctrl+F", "Buscar en la página"),
    ("Ctrl++ / Ctrl+- / Ctrl+0", "Zoom"),
    ("Ctrl+Shift+I", "Herramientas de desarrollo"),
    ("Ctrl+Shift+P", "Imprimir / guardar como PDF"),
    ("F11", "Pantalla completa"),
    ("Ctrl+Tab", "Siguiente pestaña"),
    ("Ctrl+1…9", "Ir a la pestaña n"),
]


class AboutDialog(QDialog):
    def __init__(self, info: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Acerca de {APP_NAME}")
        self.resize(560, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        name = QLabel(APP_NAME)
        name.setObjectName("PanelTitle")
        layout.addWidget(name)

        summary = QLabel(
            "Navegador con interfaz propia sobre el motor <b>Chromium</b> que incluye "
            "Qt WebEngine. Todo funciona en local: no hay servicios externos ni telemetría."
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)

        for key, value in info.items():
            layout.addWidget(QLabel(f"<b>{key}:</b> {value}"))

        keys_title = QLabel("Atajos de teclado")
        keys_title.setObjectName("PanelTitle")
        layout.addWidget(keys_title)

        keys = "".join(
            f"<tr><td style='padding-right:14px'><code>{shortcut}</code></td><td>{action}</td></tr>"
            for shortcut, action in ABOUT_KEYS
        )
        table = QLabel(f"<table>{keys}</table>")
        table.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(table)

        layout.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
