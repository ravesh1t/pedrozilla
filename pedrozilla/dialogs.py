"""Diálogos: historial, marcadores, ajustes y acerca de."""

from __future__ import annotations

import time
from typing import Any, Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QTimer, Qt, QUrl
from PySide6.QtWebEngineCore import QWebEnginePermission
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
    QListWidget,
    QStackedWidget,
    QMessageBox,
    QPushButton,
    QTableView,
    QTabWidget,
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


class _TableModel(QAbstractTableModel):
    """Modelo de solo lectura para los listados.

    QTableWidget crea un objeto por celda (32.000 para un historial de 8.000
    entradas). Con 8.000 filas, abrir el diálogo tardaba ~0,7 s y gastaba
    mucha memoria; un modelo devuelve los datos bajo demanda y solo pinta las
    filas visibles.
    """

    def __init__(self, columns: tuple[str, ...], parent=None) -> None:
        super().__init__(parent)
        self._columns = columns
        self._rows: list[tuple[list[str], str]] = []

    def set_rows(self, rows: list[tuple[list[str], str]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        values, url = self._rows[index.row()]
        column = index.column()
        if role == Qt.ItemDataRole.UserRole:
            return url
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return values[column] if column < len(values) else ""
        return None

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and 0 <= section < len(self._columns)
        ):
            return self._columns[section]
        return None

    def url_at(self, row: int) -> str:
        if 0 <= row < len(self._rows):
            return self._rows[row][1]
        return ""


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
        # Filtrar miles de entradas en cada pulsación congela la tabla;
        # esperamos a que el usuario deje de escribir.
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(180)
        self._refresh_timer.timeout.connect(self.refresh)
        self.search.textChanged.connect(self._schedule_refresh)
        layout.addWidget(self.search)

        self.model = _TableModel(self.columns, self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.doubleClicked.connect(lambda _index: self.open_current(False))
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
        index = self.table.currentIndex()
        return index.row() if index.isValid() else -1

    def current_url(self) -> str:
        return self.model.url_at(self.current_row())

    def _schedule_refresh(self) -> None:
        self._refresh_timer.start()

    def set_rows(self, rows: list[tuple[list[str], str]]) -> None:
        """rows: [([columnas...], url), ...]"""
        self.model.set_rows(rows)
        self.hint.setVisible(not rows)

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
        current = self.model.index(row, 0).data() or ""
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

        self.setWindowTitle("Ajustes de Pedrozilla")
        self.resize(840, 580)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        search_row = QHBoxLayout()
        search_icon = QLabel("🔎")
        self.search_box = QLineEdit()
        self.search_box.setObjectName("SettingsSearch")
        self.search_box.setPlaceholderText("Buscar ajustes…")
        self.search_box.setClearButtonEnabled(True)
        search_row.addWidget(search_icon)
        search_row.addWidget(self.search_box, 1)
        layout.addLayout(search_row)

        body = QHBoxLayout()
        body.setSpacing(14)
        self.category_list = QListWidget()
        self.category_list.setObjectName("SettingsSidebar")
        self.category_list.setFixedWidth(196)
        self.category_list.currentRowChanged.connect(self._show_category)
        body.addWidget(self.category_list)

        self.pages = QStackedWidget()
        self.pages.setObjectName("DialogPages")
        body.addWidget(self.pages, 1)
        layout.addLayout(body, 1)

        self._add_category("General", self._general_tab())
        self._add_category("Apariencia", self._appearance_tab())
        self._add_category("Página de inicio", self._info_page(
            "Página de inicio",
            [
                "La nueva pestaña incluye reloj, fecha, saludo, buscador, accesos "
                "directos y nota rápida.",
                "Pulsa el botón ⚙ de la esquina superior derecha para elegir el "
                "fondo, la distribución, el tamaño del reloj y los widgets visibles.",
                "Los accesos se pueden reordenar arrastrándolos y se guardan en "
                "el perfil local.",
            ],
        ))
        self._add_category("Pestañas", self._info_page(
            "Pestañas",
            [
                "Clic derecho sobre una pestaña: fijar, silenciar, agrupar, "
                "duplicar o dividir la vista.",
                "Alt+P fija o desfija · Alt+M silencia · Alt+G crea un grupo · "
                "Alt+Shift+G gestiona los grupos.",
                "Alt+V divide la pestaña actual en dos vistas independientes. "
                "El historial ofrece una lista de pestañas cerradas.",
            ],
        ))
        self._add_category("Búsqueda", self._search_tab())
        self._add_category("Privacidad y seguridad", self._privacy_tab())
        self._add_category("Descargas", self._downloads_tab())
        self._add_category("Extensiones", self._info_page(
            "Extensiones",
            [
                "Pedrozilla admite extensiones Manifest V3 en perfiles normales.",
                "Pulsa Ctrl+Shift+E o usa Ajustes → Extensiones para instalarlas "
                "y gestionarlas.",
                "Las ventanas privadas no cargan extensiones.",
            ],
        ))
        self._add_category("Espacios de trabajo", self._info_page(
            "Espacios de trabajo",
            [
                "Cada espacio guarda sus pestañas, grupos y color identificativo.",
                "Usa el menú Espacios o Alt+W para cambiar de espacio sin perder "
                "los demás.",
                "Los espacios no están disponibles en ventanas privadas.",
            ],
        ))
        self._add_category("Avanzado", self._advanced_tab())
        self._add_category("Acerca de Pedrozilla", self._info_page(
            "Acerca de Pedrozilla",
            [
                f"{APP_NAME} es un navegador local basado en Chromium (Qt WebEngine).",
                "Sin cuentas, sin sincronización obligatoria y sin telemetría.",
                "Licencia MIT. Consulta el menú Ayuda para ver la versión exacta.",
            ],
        ))

        self.search_box.textChanged.connect(self._filter_settings)
        self.category_list.setCurrentRow(0)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -- páginas -------------------------------------------------------------
    def _add_category(self, title: str, page: QWidget) -> None:
        self.category_list.addItem(title)
        self.pages.addWidget(page)

    def _info_page(self, title: str, lines: list[str]) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName("PanelTitle")
        form.addWidget(heading)
        for line in lines:
            label = QLabel(line)
            label.setWordWrap(True)
            form.addWidget(label)
        form.addStretch(1)
        return page

    def _show_category(self, row: int) -> None:
        if row >= 0:
            self.pages.setCurrentIndex(row)

    @staticmethod
    def _page_rows(page: QWidget) -> list[list[QWidget]]:
        """Agrupa cada etiqueta con el control siguiente para poder filtrarlos."""
        layout = page.layout()
        if layout is None:
            return []
        rows: list[list[QWidget]] = []
        current: list[QWidget] = []
        for index in range(layout.count()):
            item = layout.itemAt(index)
            widget = item.widget()
            if widget is None and item.layout() is not None:
                sub = item.layout()
                widget = sub.itemAt(0).widget() if sub.count() else None
            if widget is None:
                continue
            current.append(widget)
            if isinstance(widget, (QComboBox, QLineEdit, QCheckBox, QDoubleSpinBox, QPushButton)):
                rows.append(current)
                current = []
        if current:
            rows.append(current)
        return rows

    def _filter_settings(self, text: str) -> None:
        query = text.strip().lower()
        for row_index in range(self.pages.count()):
            page = self.pages.widget(row_index)
            visible_rows = 0
            for widgets in self._page_rows(page):
                content = " ".join(
                    widget.text().lower()
                    for widget in widgets
                    if hasattr(widget, "text")
                )
                visible = not query or query in content
                for widget in widgets:
                    widget.setVisible(visible)
                visible_rows += int(visible)
            self.category_list.item(row_index).setHidden(bool(query) and visible_rows == 0)
            if query and visible_rows == 0 and self.category_list.currentRow() == row_index:
                for index in range(self.category_list.count()):
                    if not self.category_list.item(index).isHidden():
                        self.category_list.setCurrentRow(index)
                        break

    def _general_tab(self) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)

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

        self.check_updates = QCheckBox("Buscar actualizaciones automáticamente en GitHub")
        self.check_updates.setChecked(bool(self.settings.get("check_updates", True)))
        form.addWidget(self.check_updates)

        form.addStretch(1)
        return page

    def _search_tab(self) -> QWidget:
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

        note = QLabel(
            "También puedes cambiar el motor desde el buscador de la nueva "
            "pestaña. La elección se guarda en el perfil local."
        )
        note.setWordWrap(True)
        note.setObjectName("MutedHint")
        form.addWidget(note)
        form.addStretch(1)
        return page

    def _downloads_tab(self) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)

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

    def _privacy_tab(self) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)

        self.javascript = QCheckBox("Permitir JavaScript")
        self.javascript.setChecked(bool(self.settings.get("javascript")))
        form.addWidget(self.javascript)

        self.ignore_certs = QCheckBox("Ignorar errores de certificado (¡inseguro!)")
        self.ignore_certs.setChecked(bool(self.settings.get("ignore_certificate_errors")))
        form.addWidget(self.ignore_certs)

        form.addWidget(QLabel("Política de referrer entre sitios"))
        self.referrer_policy = QComboBox()
        for label, value in (
            ("Estricta (recomendada)", "strict-origin-when-cross-origin"),
            ("Solo origen estricto", "strict-origin"),
            ("Solo el mismo sitio", "same-origin"),
            ("Ninguna referencia", "no-referrer"),
        ):
            self.referrer_policy.addItem(label, value)
        self.referrer_policy.setCurrentIndex(
            max(0, self.referrer_policy.findData(self.settings.get("privacy_referrer_policy")))
        )
        form.addWidget(self.referrer_policy)

        self.dns_prefetch = QCheckBox("Permitir resolución DNS anticipada")
        self.dns_prefetch.setChecked(bool(self.settings.get("privacy_dns_prefetch")))
        form.addWidget(self.dns_prefetch)

        self.hyperlink_auditing = QCheckBox("Permitir auditoría de enlaces (ping)")
        self.hyperlink_auditing.setChecked(bool(self.settings.get("privacy_hyperlink_auditing")))
        form.addWidget(self.hyperlink_auditing)

        self.insecure_geolocation = QCheckBox("Permitir geolocalización en sitios HTTP")
        self.insecure_geolocation.setChecked(bool(self.settings.get("privacy_insecure_geolocation")))
        form.addWidget(self.insecure_geolocation)

        self.local_remote_urls = QCheckBox("Permitir que archivos locales accedan a la red")
        self.local_remote_urls.setChecked(bool(self.settings.get("privacy_local_remote_urls")))
        form.addWidget(self.local_remote_urls)

        warning = QLabel(
            "El centro de privacidad (menú Ajustes) permite revisar permisos, "
            "borrar cookies y consultar el estado de los certificados del sitio actual. "
            "Qt WebEngine no expone la cabecera Do Not Track ni una API directa de "
            "referrer: la política se aplica mediante una etiqueta meta local."
        )
        warning.setObjectName("MutedHint")
        warning.setWordWrap(True)
        form.addWidget(warning)

        if self._clear_data is not None:
            clear = QPushButton("Borrar datos de navegación (cookies, caché, historial)…")
            clear.clicked.connect(self._clear_data)
            form.addWidget(clear)
        form.addStretch(1)
        return page

    def _appearance_tab(self) -> QWidget:
        page = QWidget()
        form = QVBoxLayout(page)
        form.setSpacing(10)

        form.addWidget(QLabel("Tema de la interfaz"))
        self.theme = QComboBox()
        self.theme.addItem("Moderno (Pedrozilla Modern)", "modern")
        self.theme.addItem("Clásico (Firefox 7)", "classic")
        self.theme.addItem("Oscuro", "dark")
        self.theme.addItem("Claro", "light")
        theme_val = self.settings.get("theme") or "classic"
        self.theme.setCurrentIndex(max(0, self.theme.findData(theme_val)))
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

        form.addWidget(QLabel("Tamaño de letra del modo lectura (px)"))
        self.reader_font = QDoubleSpinBox()
        self.reader_font.setRange(12, 36)
        self.reader_font.setSingleStep(1)
        self.reader_font.setDecimals(0)
        self.reader_font.setValue(float(self.settings.get("reader_font_size", 19)))
        form.addWidget(self.reader_font)

        form.addWidget(QLabel("Ancho del texto en modo lectura (px)"))
        self.reader_width_box = QDoubleSpinBox()
        self.reader_width_box.setRange(480, 1400)
        self.reader_width_box.setSingleStep(20)
        self.reader_width_box.setDecimals(0)
        self.reader_width_box.setValue(float(self.settings.get("reader_width", 720)))
        form.addWidget(self.reader_width_box)

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

        warning = QLabel(
            "Cambiar el user agent requiere recargar las pestañas abiertas. "
            "JavaScript y los certificados se ajustan en «Privacidad y seguridad»."
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
        self.check_updates.setChecked(DEFAULT_SETTINGS["check_updates"])
        self.theme.setCurrentIndex(max(0, self.theme.findData(DEFAULT_SETTINGS["theme"])))
        self.show_bookmarks.setChecked(DEFAULT_SETTINGS["show_bookmarks_bar"])
        self.zoom.setValue(DEFAULT_SETTINGS["default_zoom"] * 100)
        self.reader_font.setValue(DEFAULT_SETTINGS["reader_font_size"])
        self.reader_width_box.setValue(DEFAULT_SETTINGS["reader_width"])
        self.user_agent.setText(DEFAULT_SETTINGS["user_agent"])
        self.javascript.setChecked(DEFAULT_SETTINGS["javascript"])
        self.ignore_certs.setChecked(DEFAULT_SETTINGS["ignore_certificate_errors"])
        self.referrer_policy.setCurrentIndex(
            max(0, self.referrer_policy.findData(DEFAULT_SETTINGS["privacy_referrer_policy"]))
        )
        self.dns_prefetch.setChecked(DEFAULT_SETTINGS["privacy_dns_prefetch"])
        self.hyperlink_auditing.setChecked(DEFAULT_SETTINGS["privacy_hyperlink_auditing"])
        self.insecure_geolocation.setChecked(DEFAULT_SETTINGS["privacy_insecure_geolocation"])
        self.local_remote_urls.setChecked(DEFAULT_SETTINGS["privacy_local_remote_urls"])

    def values(self) -> dict[str, Any]:
        return {
            "search_engine": self.engine.currentData(),
            "homepage": self.homepage.text().strip(),
            "startup": self.startup.currentData(),
            "download_dir": self.download_dir.text().strip(),
            "ask_download_dir": self.ask_dir.isChecked(),
            "check_updates": self.check_updates.isChecked(),
            "theme": self.theme.currentData(),
            "show_bookmarks_bar": self.show_bookmarks.isChecked(),
            "default_zoom": round(self.zoom.value() / 100, 2),
            "reader_font_size": int(self.reader_font.value()),
            "reader_width": int(self.reader_width_box.value()),
            "user_agent": self.user_agent.text().strip(),
            "javascript": self.javascript.isChecked(),
            "ignore_certificate_errors": self.ignore_certs.isChecked(),
            "privacy_referrer_policy": self.referrer_policy.currentData(),
            "privacy_dns_prefetch": self.dns_prefetch.isChecked(),
            "privacy_hyperlink_auditing": self.hyperlink_auditing.isChecked(),
            "privacy_insecure_geolocation": self.insecure_geolocation.isChecked(),
            "privacy_local_remote_urls": self.local_remote_urls.isChecked(),
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
    ("Ctrl+Shift+E", "Gestor de extensiones"),
    ("Ctrl+,", "Preferencias"),
    ("F9", "Modo lectura"),
    ("Alt+V", "Vista dividida"),
    ("Alt+P / Alt+M", "Fijar / silenciar pestaña"),
    ("Alt+G / Alt+Shift+G", "Crear / gestionar grupos de pestañas"),
    ("Alt+W", "Cambiar de espacio de trabajo"),
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


class PrivacyDialog(QDialog):
    """Centro de privacidad del sitio actual.

    Solo muestra controles que Qt WebEngine expone de verdad. Cuando una API no
    existe (por ejemplo, enumerar cookies), se indica la limitación en lugar de
    mostrar un indicador de protección fingido.
    """

    def __init__(
        self,
        profile,
        settings,
        url: str,
        cert_info: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.profile = profile
        self.settings = settings
        self.url = url or ""
        self.setWindowTitle("Centro de privacidad")
        self.resize(580, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel("Centro de privacidad")
        title.setObjectName("PanelTitle")
        layout.addWidget(title)

        origin = QUrl(self.url)
        host = origin.host() if origin.isValid() else ""
        site = host or self.url or "Página local"
        layout.addWidget(QLabel(f"<b>Sitio:</b> {site}"))

        # -- Permisos reales del origen -------------------------------------
        perm_title = QLabel("Permisos del sitio")
        perm_title.setObjectName("PanelTitle")
        layout.addWidget(perm_title)

        self.perm_rows: list[tuple[QWebEnginePermission, QLabel]] = []
        permissions = []
        try:
            permissions = list(self.profile.listPermissionsForOrigin(origin)) if host else []
        except Exception:
            permissions = []

        if not permissions:
            empty = QLabel(
                "No hay permisos concedidos o denegados guardados para este origen. "
                "Cámara, micrófono, notificaciones y ubicación se solicitarán cuando "
                "la página lo pida."
            )
            empty.setWordWrap(True)
            layout.addWidget(empty)
        for permission in permissions:
            row = QHBoxLayout()
            name = QLabel(self._permission_name(permission.permissionType()))
            name.setMinimumWidth(180)
            state = QLabel(self._state_name(permission.state()))
            state.setMinimumWidth(70)
            row.addWidget(name)
            row.addWidget(state, 1)
            for text, action in (
                ("Permitir", permission.grant),
                ("Denegar", permission.deny),
                ("Restablecer", permission.reset),
            ):
                button = QPushButton(text)
                button.clicked.connect(lambda _checked=False, fn=action, lbl=state: self._apply_permission(fn, lbl))
                row.addWidget(button)
            layout.addLayout(row)
            self.perm_rows.append((permission, state))

        # -- JavaScript ------------------------------------------------------
        js_title = QLabel("Contenido y scripts")
        js_title.setObjectName("PanelTitle")
        layout.addWidget(js_title)
        self.js_check = QCheckBox("Permitir JavaScript")
        self.js_check.setChecked(bool(self.settings.get("javascript", True)))
        self.js_check.toggled.connect(self._toggle_javascript)
        layout.addWidget(self.js_check)
        hint = QLabel("El cambio se aplica a las páginas que se abran a partir de ahora.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # -- Cookies y almacenamiento ---------------------------------------
        storage_title = QLabel("Cookies y almacenamiento local")
        storage_title.setObjectName("PanelTitle")
        layout.addWidget(storage_title)
        limit = QLabel(
            "Qt WebEngine no expone una API para enumerar las cookies de un sitio. "
            "Puedes borrarlas todas o solo las de sesión con los botones siguientes."
        )
        limit.setWordWrap(True)
        layout.addWidget(limit)

        cookie_row = QHBoxLayout()
        session_button = QPushButton("Borrar cookies de sesión")
        session_button.clicked.connect(self._delete_session_cookies)
        all_button = QPushButton("Borrar todas las cookies")
        all_button.clicked.connect(self._delete_all_cookies)
        cookie_row.addWidget(session_button)
        cookie_row.addWidget(all_button)
        layout.addLayout(cookie_row)

        cache_button = QPushButton("Borrar caché HTTP")
        cache_button.clicked.connect(self._clear_cache)
        layout.addWidget(cache_button)

        storage_label = QLabel(
            f"Datos persistentes: <code>{self.profile.persistentStoragePath()}</code><br>"
            f"Caché: <code>{self.profile.cachePath()}</code>"
        )
        storage_label.setTextFormat(Qt.TextFormat.RichText)
        storage_label.setWordWrap(True)
        layout.addWidget(storage_label)

        # -- Certificados ----------------------------------------------------
        cert_title = QLabel("Certificados y seguridad")
        cert_title.setObjectName("PanelTitle")
        layout.addWidget(cert_title)
        cert = QLabel(cert_info or "No se han registrado errores de certificado recientes para este sitio.")
        cert.setWordWrap(True)
        layout.addWidget(cert)

        layout.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    @staticmethod
    def _permission_name(kind) -> str:
        names = {
            "Geolocation": "Ubicación",
            "MediaAudioCapture": "Micrófono",
            "MediaVideoCapture": "Cámara",
            "MediaAudioVideoCapture": "Cámara y micrófono",
            "DesktopVideoCapture": "Captura de pantalla",
            "DesktopAudioVideoCapture": "Captura de pantalla y audio",
            "Notifications": "Notificaciones",
            "MouseLock": "Bloqueo del ratón",
            "ClipboardReadWrite": "Portapapeles",
            "LocalFontsAccess": "Fuentes locales",
        }
        key = getattr(kind, "name", str(kind))
        return names.get(key, key)

    @staticmethod
    def _state_name(state) -> str:
        names = {
            "Ask": "Preguntar",
            "Granted": "Permitido",
            "Denied": "Denegado",
            "Invalid": "No válido",
        }
        key = getattr(state, "name", str(state))
        return names.get(key, key)

    def _apply_permission(self, action, label: QLabel) -> None:
        try:
            action()
        except Exception as exc:
            QMessageBox.warning(self, "Permisos", f"No se pudo cambiar el permiso: {exc}")
            return
        # El estado de QWebEnginePermission es inmutable; volver a consultar el
        # perfil es la única forma fiable de reflejar el cambio.
        del label
        self._refresh_permissions()

    def _refresh_permissions(self) -> None:
        try:
            permissions = list(self.profile.listPermissionsForOrigin(QUrl(self.url)))
        except Exception:
            return
        for permission, label in self.perm_rows:
            for fresh in permissions:
                if (
                    fresh.origin() == permission.origin()
                    and fresh.permissionType() == permission.permissionType()
                ):
                    label.setText(self._state_name(fresh.state()))
                    break

    def _toggle_javascript(self, checked: bool) -> None:
        self.settings.set("javascript", bool(checked))

    def _delete_session_cookies(self) -> None:
        self.profile.cookieStore().deleteSessionCookies()
        QMessageBox.information(self, "Cookies", "Se han borrado las cookies de sesión.")

    def _delete_all_cookies(self) -> None:
        answer = QMessageBox.question(
            self,
            "Cookies",
            "¿Borrar todas las cookies de todos los sitios?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.profile.cookieStore().deleteAllCookies()
            QMessageBox.information(self, "Cookies", "Se han borrado todas las cookies.")

    def _clear_cache(self) -> None:
        self.profile.clearHttpCache()
        QMessageBox.information(self, "Caché", "Se ha borrado la caché HTTP.")
