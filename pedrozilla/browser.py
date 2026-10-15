"""Ventana del navegador: pestañas, barra de direcciones, menús y todo el pegamento."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QSize, QStringListModel, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWebEngineCore import (
    QWebEngineContextMenuRequest,
    QWebEngineDownloadRequest,
    QWebEnginePage,
    QWebEnginePermission,
    QWebEngineProfile,
    QWebEngineSettings,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QCompleter,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .dialogs import AboutDialog, BookmarksDialog, HistoryDialog, SettingsDialog
from .downloads import DownloadRow, DownloadsDialog, DownloadsManager
from .newtab import new_tab_html
from .storage import Bookmarks, History, Session, Settings, config_dir, data_dir
from .utils import (
    color_for,
    decorate_user_agent,
    display_url,
    host_of,
    initial_letter,
    is_web_url,
    normalize_input,
    truncate,
)
from .webview import WebView

BRAND = "Pedrozilla"

_PERMISSION_LABELS = {
    QWebEnginePermission.PermissionType.MediaAudioCapture: "el micrófono",
    QWebEnginePermission.PermissionType.MediaVideoCapture: "la cámara",
    QWebEnginePermission.PermissionType.MediaAudioVideoCapture: "la cámara y el micrófono",
    QWebEnginePermission.PermissionType.DesktopVideoCapture: "capturar la pantalla",
    QWebEnginePermission.PermissionType.DesktopAudioVideoCapture: "capturar pantalla y audio",
    QWebEnginePermission.PermissionType.Geolocation: "tu ubicación",
    QWebEnginePermission.PermissionType.Notifications: "enviar notificaciones",
    QWebEnginePermission.PermissionType.ClipboardReadWrite: "el portapapeles",
    QWebEnginePermission.PermissionType.MouseLock: "bloquear el puntero",
    QWebEnginePermission.PermissionType.LocalFontsAccess: "las fuentes locales",
}


def brand_icon(size: int = 64) -> QIcon:
    """Icono del navegador dibujado en memoria (sin archivos externos)."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#8ab4f8"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.setPen(QColor("#202124"))
    font = QFont()
    font.setPixelSize(int(size * 0.56))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, BRAND[0].upper())
    painter.end()
    return QIcon(pixmap)


def _letter_icon(text: str, color_source: str = "", size: int = 20) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color_for(color_source or text)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.setPen(QColor("#202124"))
    font = QFont()
    font.setPixelSize(max(9, int(size * 0.55)))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initial_letter(text))
    painter.end()
    return QIcon(pixmap)


class BrowserContext:
    """Estado compartido: ajustes, historial, marcadores, perfiles y ventanas."""

    def __init__(self, settings: Settings, history: History, bookmarks: Bookmarks) -> None:
        self.settings = settings
        self.history = history
        self.bookmarks = bookmarks
        self.downloads = DownloadsManager(settings)
        self.session = Session()
        self.windows: list[BrowserWindow] = []
        self.closed_tabs: list[dict[str, str]] = []
        self.default_user_agent = ""
        self.chromium_version = "desconocida"
        self.persistent_profile: QWebEngineProfile | None = None
        self._attached_profiles: set[int] = set()

    # -- perfiles -----------------------------------------------------------
    def build_persistent_profile(self) -> QWebEngineProfile:
        data_root = data_dir()
        # El "perfil por defecto" de Qt WebEngine debe tener rutas propias: si no,
        # Qt crea su carpeta QtWebEngine (~/.local/share/<Org>/<App> en Linux,
        # %LOCALAPPDATA%\<Org>\<App> en Windows) fuera de nuestro directorio.
        default_profile = QWebEngineProfile.defaultProfile()
        default_profile.setPersistentStoragePath(str(data_root / "default-profile"))
        default_profile.setCachePath(str(data_root / "default-cache"))
        self.default_user_agent = default_profile.httpUserAgent()
        self.chromium_version = self._chromium_from_ua(self.default_user_agent)

        profile = QWebEngineProfile("pedrozilla", QApplication.instance())
        profile.setPersistentStoragePath(str(data_root / "profile"))
        profile.setCachePath(str(data_root / "cache"))
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        profile.setHttpCacheMaximumSize(200 * 1024 * 1024)
        self.persistent_profile = profile
        self.configure_profile(default_profile)
        self.configure_profile(profile)
        return profile

    @staticmethod
    def _chromium_from_ua(user_agent: str) -> str:
        for token in (user_agent or "").split():
            if token.startswith("Chrome/"):
                return token.split("/", 1)[1]
        return "desconocida"

    def configure_profile(self, profile: QWebEngineProfile) -> None:
        user_agent = self.settings.get("user_agent") or decorate_user_agent(self.default_user_agent)
        if user_agent:
            profile.setHttpUserAgent(user_agent)
        if id(profile) not in self._attached_profiles:
            self.downloads.attach(profile)
            self._attached_profiles.add(id(profile))

    def new_off_the_record_profile(self) -> QWebEngineProfile:
        """Perfil sin nombre: no guarda cookies, caché ni historial."""
        profile = QWebEngineProfile(QApplication.instance())
        self.configure_profile(profile)
        return profile

    # -- ventanas -----------------------------------------------------------
    def open_window(self, incognito: bool = False, urls: list[str] | None = None) -> "BrowserWindow":
        profile = self.new_off_the_record_profile() if incognito else self.persistent_profile
        window = BrowserWindow(self, profile, incognito=incognito)
        window.open_initial_tabs(list(urls or []))
        self.windows.append(window)
        window.show()
        window.raise_()
        return window

    def forget_window(self, window: "BrowserWindow") -> None:
        if window in self.windows:
            self.windows.remove(window)


class BrowserWindow(QMainWindow):
    """Una ventana con sus pestañas."""

    fullscreen_changed = Signal(bool)

    def __init__(
        self, context: BrowserContext, profile: QWebEngineProfile, incognito: bool = False
    ) -> None:
        super().__init__()
        self.context = context
        self.settings = context.settings
        self.history = context.history
        self.bookmarks = context.bookmarks
        self.downloads = context.downloads
        self.profile = profile
        self.incognito = incognito
        self.ignore_certificate_errors = bool(self.settings.get("ignore_certificate_errors"))
        self.debug_console = False

        self._devtools_view: QWebEngineView | None = None
        self._devtools_page: QWebEnginePage | None = None
        self._html_fullscreen = False
        self._cert_warned: set[str] = set()

        self.setWindowIcon(brand_icon())
        self.resize(1280, 840)
        self.setMinimumSize(600, 420)

        self._build_central()
        self._build_toolbar()
        self._build_bookmarks_bar()
        self._build_menus()
        self._build_shortcuts()
        self._build_status_bar()

        self.bookmarks.changed.connect(self._rebuild_bookmarks_bar)
        self.bookmarks.changed.connect(self._refresh_completions)
        self.history.changed.connect(self._refresh_completions)
        self.downloads.started.connect(self._on_download_started)
        self.downloads.updated.connect(lambda _download: self._refresh_downloads_button())
        self._refresh_completions()

    # --------------------------------------------------------------- montaje
    def _build_central(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.find_bar = self._make_find_bar()
        layout.addWidget(self.find_bar)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().installEventFilter(self)
        self.tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self._show_tab_menu)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs, 1)

        self.downloads_bar = self._make_downloads_bar()
        layout.addWidget(self.downloads_bar)

        self.setCentralWidget(central)

    def _make_find_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("FindBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self.find_input = QLineEdit()
        self.find_input.setObjectName("FindInput")
        self.find_input.setPlaceholderText("Buscar en la página…")
        self.find_input.setMinimumWidth(280)
        self.find_input.textChanged.connect(self._find_changed)
        self.find_input.installEventFilter(self)
        layout.addWidget(self.find_input, 1)

        self.find_count = QLabel("")
        self.find_count.setObjectName("MutedHint")
        self.find_count.setMinimumWidth(80)
        layout.addWidget(self.find_count)

        previous = QPushButton("↑")
        previous.setToolTip("Coincidencia anterior (Shift+Enter)")
        previous.setMaximumWidth(44)
        previous.clicked.connect(lambda: self.find_next(True))
        layout.addWidget(previous)

        following = QPushButton("↓")
        following.setToolTip("Coincidencia siguiente (Enter)")
        following.setMaximumWidth(44)
        following.clicked.connect(lambda: self.find_next(False))
        layout.addWidget(following)

        close = QPushButton("✕")
        close.setToolTip("Cerrar (Esc)")
        close.setMaximumWidth(44)
        close.clicked.connect(self.close_find_bar)
        layout.addWidget(close)

        bar.setVisible(False)
        return bar

    def _make_downloads_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("DownloadsBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        self._downloads_row_host = QWidget()
        self._downloads_row_layout = QVBoxLayout(self._downloads_row_host)
        self._downloads_row_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._downloads_row_host, 1)

        show_all = QPushButton("Ver todas las descargas")
        show_all.clicked.connect(self.show_downloads)
        layout.addWidget(show_all)

        hide = QPushButton("✕")
        hide.setMaximumWidth(44)
        hide.clicked.connect(lambda: bar.setVisible(False))
        layout.addWidget(hide)

        bar.setVisible(False)
        return bar

    def _toolbar_button(self, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setAutoRaise(True)
        button.setIconSize(QSize(18, 18))
        return button

    def _build_toolbar(self) -> None:
        self.toolbar = QToolBar("Principal")
        self.toolbar.setObjectName("MainToolBar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.action_back = self._action("◀", "Atrás (Alt+←)", self.go_back)
        self.action_forward = self._action("▶", "Adelante (Alt+→)", self.go_forward)
        self.action_reload = self._action("⟳", "Recargar (Ctrl+R)", self.reload_or_stop)
        self.action_home = self._action("⌂", "Página de inicio", self.go_home)
        for action in (self.action_back, self.action_forward, self.action_reload, self.action_home):
            self.toolbar.addWidget(self._toolbar_button(action))

        self.omnibox = QLineEdit()
        self.omnibox.setObjectName("Omnibox")
        self.omnibox.setPlaceholderText("Buscar o escribir una dirección")
        self.omnibox.setClearButtonEnabled(True)
        self.omnibox.setMinimumWidth(320)
        self.omnibox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.omnibox.returnPressed.connect(self._navigate_from_omnibox)
        self.omnibox.installEventFilter(self)

        self._completion_model = QStringListModel(self)
        self._completer = QCompleter(self._completion_model, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setMaxVisibleItems(10)
        self._completer.activated.connect(self._completion_chosen)
        self.omnibox.setCompleter(self._completer)
        self.toolbar.addWidget(self.omnibox)

        self.action_star = self._action("☆", "Guardar en marcadores (Ctrl+D)", self.toggle_bookmark)
        self._star_button = self._toolbar_button(self.action_star)
        self.toolbar.addWidget(self._star_button)

        self.action_downloads = self._action("⭳", "Descargas (Ctrl+J)", self.show_downloads)
        self._downloads_button = self._toolbar_button(self.action_downloads)
        self.toolbar.addWidget(self._downloads_button)

        self.action_menu = self._action("☰", "Menú principal", self._show_main_menu)
        self._menu_button = self._toolbar_button(self.action_menu)
        self.toolbar.addWidget(self._menu_button)

    def _action(self, text: str, tooltip: str, slot, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        action.setToolTip(tooltip)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        return action

    def _build_bookmarks_bar(self) -> None:
        self.bookmarks_bar = QToolBar("Marcadores")
        self.bookmarks_bar.setObjectName("BookmarksBar")
        self.bookmarks_bar.setMovable(False)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.bookmarks_bar)
        self.bookmarks_bar.setVisible(bool(self.settings.get("show_bookmarks_bar")))
        self._rebuild_bookmarks_bar()

    def _build_status_bar(self) -> None:
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setMaximumWidth(200)
        self.progress.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress)
        self.statusBar().showMessage("Listo")

    def _menu(self, title: str) -> QMenu:
        return self.menuBar().addMenu(title)

    def _add(self, container, text: str, slot, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        container.addAction(action)
        return action

    def _add_page_action(self, menu, text: str, web_action, shortcut=None) -> QAction:
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(QKeySequence(shortcut) if isinstance(shortcut, str) else QKeySequence(shortcut))
        action.triggered.connect(lambda: self.trigger_page_action(web_action))
        menu.addAction(action)
        return action

    def _build_menus(self) -> None:
        self.menuBar().setNativeMenuBar(False)

        file_menu = self._menu("&Archivo")
        self._add(file_menu, "Nueva pestaña", self.new_tab_focused, "Ctrl+T")
        self._add(file_menu, "Nueva ventana", lambda: self.context.open_window(), "Ctrl+N")
        self._add(
            file_menu,
            "Nueva ventana privada",
            lambda: self.context.open_window(incognito=True),
            "Ctrl+Shift+N",
        )
        file_menu.addSeparator()
        self._add(file_menu, "Abrir archivo local…", self.open_local_file, "Ctrl+O")
        self._add(file_menu, "Guardar página como…", self.save_page, "Ctrl+S")
        self._add(file_menu, "Guardar como PDF…", self.save_pdf)
        self._add(file_menu, "Imprimir…", self.print_page, "Ctrl+Shift+P")
        file_menu.addSeparator()
        self._add(file_menu, "Cerrar pestaña", lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        self._add(file_menu, "Salir", self.close_all_windows, "Ctrl+Q")

        edit_menu = self._menu("&Editar")
        self._add_page_action(edit_menu, "Deshacer", QWebEnginePage.WebAction.Undo, QKeySequence.StandardKey.Undo)
        self._add_page_action(edit_menu, "Rehacer", QWebEnginePage.WebAction.Redo, QKeySequence.StandardKey.Redo)
        edit_menu.addSeparator()
        self._add_page_action(edit_menu, "Cortar", QWebEnginePage.WebAction.Cut, QKeySequence.StandardKey.Cut)
        self._add_page_action(edit_menu, "Copiar", QWebEnginePage.WebAction.Copy, QKeySequence.StandardKey.Copy)
        self._add_page_action(edit_menu, "Pegar", QWebEnginePage.WebAction.Paste, QKeySequence.StandardKey.Paste)
        self._add_page_action(
            edit_menu,
            "Seleccionar todo",
            QWebEnginePage.WebAction.SelectAll,
            QKeySequence.StandardKey.SelectAll,
        )
        edit_menu.addSeparator()
        self._add(edit_menu, "Buscar en la página…", self.open_find_bar, "Ctrl+F")

        view_menu = self._menu("&Ver")
        self._add(view_menu, "Recargar", self.reload_or_stop, "Ctrl+R")
        self._add(view_menu, "Recargar sin caché", self.hard_reload, "Ctrl+Shift+R")
        self._add(view_menu, "Detener", self.stop_loading)
        view_menu.addSeparator()
        self._add(view_menu, "Aumentar zoom", lambda: self.change_zoom(0.1), "Ctrl++")
        self._add(view_menu, "Reducir zoom", lambda: self.change_zoom(-0.1), "Ctrl+-")
        self._add(view_menu, "Zoom original", lambda: self.set_zoom(1.0), "Ctrl+0")
        view_menu.addSeparator()
        self.action_show_bookmarks = QAction("Barra de marcadores", self)
        self.action_show_bookmarks.setCheckable(True)
        self.action_show_bookmarks.setChecked(bool(self.settings.get("show_bookmarks_bar")))
        self.action_show_bookmarks.setShortcut(QKeySequence("Ctrl+Shift+B"))
        self.action_show_bookmarks.toggled.connect(self._toggle_bookmarks_bar)
        view_menu.addAction(self.action_show_bookmarks)
        self._add(view_menu, "Pantalla completa", self.toggle_fullscreen, "F11")
        view_menu.addSeparator()
        self._add_page_action(view_menu, "Código fuente", QWebEnginePage.WebAction.ViewSource, "Ctrl+U")
        self._add(view_menu, "Herramientas de desarrollo", self.open_devtools, "Ctrl+Shift+I")

        history_menu = self._menu("&Historial")
        self._add(history_menu, "Atrás", self.go_back)
        self._add(history_menu, "Adelante", self.go_forward)
        self._add(history_menu, "Página de inicio", self.go_home)
        history_menu.addSeparator()
        self._add(history_menu, "Mostrar historial", self.show_history, "Ctrl+H")
        self._add(history_menu, "Reabrir última pestaña cerrada", self.reopen_closed_tab, "Ctrl+Shift+T")
        history_menu.addSeparator()
        self._add(history_menu, "Borrar datos de navegación…", self.clear_browsing_data)

        bookmarks_menu = self._menu("&Marcadores")
        self._add(bookmarks_menu, "Guardar o quitar marcador", self.toggle_bookmark, "Ctrl+D")
        self._add(bookmarks_menu, "Mostrar todos los marcadores", self.show_bookmarks_manager, "Ctrl+Shift+O")

        self._add(self._menu("&Descargas"), "Mostrar descargas", self.show_downloads, "Ctrl+J")
        self._add(self._menu("&Ajustes"), "Preferencias…", self.show_settings, "Ctrl+,")
        self._add(self._menu("A&yuda"), f"Acerca de {BRAND}", self.show_about, "F1")

    def _build_shortcuts(self) -> None:
        self._add(self, "Atrás", self.go_back, "Alt+Left")
        self._add(self, "Adelante", self.go_forward, "Alt+Right")
        self._add(self, "Pestaña siguiente", lambda: self._cycle_tab(1), "Ctrl+Tab")
        self._add(self, "Pestaña anterior", lambda: self._cycle_tab(-1), "Ctrl+Shift+Tab")
        for number in range(1, 9):
            self._add(self, f"Pestaña {number}", lambda n=number - 1: self._focus_tab(n), f"Ctrl+{number}")

    # ------------------------------------------------------------- pestañas
    def current_view(self) -> WebView | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, WebView) else None

    def current_page(self) -> QWebEnginePage | None:
        view = self.current_view()
        return view.page() if view is not None else None

    def open_initial_tabs(self, urls: list[str]) -> None:
        targets, active = self._initial_targets(urls)
        if targets:
            for target in targets:
                # Una entrada vacía en la sesión es una pestaña en blanco.
                self.new_tab(
                    target,
                    focus=False,
                    background=True,
                    activate=False,
                    load_newtab_page=not target,
                )
            self.tabs.setCurrentIndex(max(0, min(active, self.tabs.count() - 1)))
        else:
            self.new_tab(focus=False, activate=False)

        geometry = self.context.session.geometry()
        if geometry:
            self.restoreGeometry(geometry)
        if self.context.session.data.get("maximized"):
            self.showMaximized()
        self._on_tab_changed(self.tabs.currentIndex())

    def _initial_targets(self, urls: list[str]) -> tuple[list[str], int]:
        """Decide qué pestañas abrir al arrancar y cuál queda activa.

        Una URL vacía significa "página de nueva pestaña".
        """
        template = self.settings.search_template
        if urls:
            return [normalize_input(url, template) for url in urls], len(urls) - 1

        startup = self.settings.get("startup", "newtab")
        homepage = (self.settings.get("homepage") or "").strip()

        if not self.incognito and startup == "restore":
            entries = self.context.session.data.get("tabs", [])
            targets = [str(entry.get("url") or "") for entry in entries]
            if targets:
                active = int(self.context.session.data.get("active") or 0)
                return targets, active
        if startup == "homepage" and homepage:
            return [normalize_input(homepage, template)], 0
        return [], 0

    def new_tab_focused(self) -> None:
        self.new_tab()

    def new_tab(
        self,
        url: str = "",
        *,
        focus: bool = True,
        background: bool = False,
        load_newtab_page: bool = True,
        activate: bool = True,
    ) -> WebView:
        """Crea una pestaña. `focus` enfoca la omnibox, `activate` la selecciona."""
        view = WebView(self.profile, window=self)
        self._wire_view(view)

        index = self.tabs.addTab(view, "Nueva pestaña")
        if activate and not background:
            self.tabs.setCurrentIndex(index)

        if url:
            view.load_input(url)
        elif load_newtab_page:
            self.load_new_tab_page(view)

        if focus and not background:
            self.omnibox.setFocus()
            self.omnibox.selectAll()
        return view

    def _wire_view(self, view: WebView) -> None:
        page = view.web_page
        page.set_new_tab_handler(self._handle_new_window_request)
        page.set_debug_console(self.debug_console)
        self._apply_page_settings(page)
        view.set_zoom(float(self.settings.get("default_zoom", 1.0)))

        view.titleChanged.connect(lambda title, v=view: self._on_title_changed(v, title))
        view.urlChanged.connect(lambda _url, v=view: self._on_url_changed(v))
        view.iconChanged.connect(lambda _icon, v=view: self._on_icon_changed(v))
        view.loadStarted.connect(lambda v=view: self._on_load_started(v))
        view.loadProgress.connect(lambda value, v=view: self._on_load_progress(v, value))
        view.loadFinished.connect(lambda ok, v=view: self._on_load_finished(v, ok))
        view.status_hint.connect(self._on_status_hint)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        view.customContextMenuRequested.connect(lambda pos, v=view: self._show_context_menu(v, pos))

        page.permissionRequested.connect(self._on_permission_requested)
        page.fullScreenRequested.connect(self._on_fullscreen_requested)
        page.windowCloseRequested.connect(lambda p=page: self._close_page_tab(p))
        page.printRequested.connect(self.print_page)
        page.authenticationRequired.connect(self._on_authentication_required)
        page.findTextFinished.connect(lambda result, v=view: self._on_find_finished(v, result))
        page.pdfPrintingFinished.connect(self._on_pdf_finished)
        page.renderProcessTerminated.connect(
            lambda status, code, v=view: self._on_render_terminated(v, status, code)
        )

    def _apply_page_settings(self, page: QWebEnginePage) -> None:
        settings = page.settings()
        attribute = QWebEngineSettings.WebAttribute
        settings.setAttribute(attribute.JavascriptEnabled, bool(self.settings.get("javascript")))
        settings.setAttribute(attribute.FullScreenSupportEnabled, True)
        settings.setAttribute(attribute.PdfViewerEnabled, True)
        settings.setAttribute(attribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(attribute.PlaybackRequiresUserGesture, True)
        settings.setAttribute(attribute.LocalStorageEnabled, True)
        settings.setAttribute(attribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(attribute.ScreenCaptureEnabled, True)
        settings.setAttribute(attribute.WebGLEnabled, True)
        settings.setAttribute(attribute.ErrorPageEnabled, True)
        settings.setAttribute(attribute.AllowWindowActivationFromJavaScript, False)
        settings.setAttribute(attribute.FocusOnNavigationEnabled, False)

    def load_new_tab_page(self, view: WebView) -> None:
        html = new_tab_html(
            search_template=self.settings.search_template,
            engine_key=self.settings.get("search_engine", "duckduckgo"),
            theme=self.settings.get("theme", "dark"),
            bookmarks=self.bookmarks.items(),
            brand=BRAND,
            footer=(
                "Ventana privada: no se guarda historial, cookies ni caché"
                if self.incognito
                else "Navegador basado en Chromium · Qt WebEngine"
            ),
        )
        view.load_html_page(html)

    def close_tab(self, index: int) -> None:
        if index < 0 or index >= self.tabs.count():
            return
        view = self.tabs.widget(index)
        if isinstance(view, WebView) and not view.is_new_tab_page:
            url = view.url_string()
            if is_web_url(url):
                self.context.closed_tabs.append({"url": url, "title": view.title()})
                del self.context.closed_tabs[:-20]

        self.tabs.removeTab(index)
        if isinstance(view, WebView):
            view.deleteLater()

        if self.tabs.count() == 0:
            if len(self.context.windows) <= 1:
                self.new_tab()
            else:
                self.close()

    def reopen_closed_tab(self) -> None:
        if not self.context.closed_tabs:
            self.statusBar().showMessage("No hay pestañas cerradas para reabrir", 3000)
            return
        entry = self.context.closed_tabs.pop()
        self.new_tab(entry.get("url", ""))

    def _close_page_tab(self, page: QWebEnginePage) -> None:
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            if isinstance(view, WebView) and view.page() is page:
                self.close_tab(index)
                return

    def _handle_new_window_request(self, source_page: QWebEnginePage, window_type) -> QWebEnginePage | None:
        """Chromium pide una ventana nueva: la resolvemos como pestaña."""
        view = self.new_tab(focus=False, background=True, activate=False, load_newtab_page=False)
        return view.page()

    def _cycle_tab(self, step: int) -> None:
        count = self.tabs.count()
        if count:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + step) % count)

    def _focus_tab(self, index: int) -> None:
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index)

    def _tab_url(self, index: int) -> str:
        view = self.tabs.widget(index)
        if isinstance(view, WebView) and not view.is_new_tab_page:
            url = view.url_string()
            return "" if url == "about:blank" else url
        return ""

    # ------------------------------------------------- eventos de pestaña
    def _on_tab_changed(self, index: int) -> None:
        view = self.current_view()
        if view is None:
            return
        self._update_omnibox(view)
        self._update_nav_actions(view)
        self._update_star(view)
        self._update_window_title()
        self._sync_devtools()
        if self.find_bar.isVisible() and self.find_input.text():
            self._find_changed(self.find_input.text())

    def _on_title_changed(self, view: WebView, title: str) -> None:
        self._sync_titles(view)

    def _sync_titles(self, view: WebView, dom_title: str | None = None) -> None:
        """Actualiza la pestaña y el título de la ventana con el título actual.

        No basta con `titleChanged`: Qt WebEngine a veces fija el título del
        documento sin volver a emitir la señal (y `view.title()` puede quedarse
        con la URL como valor provisional), así que al terminar cada carga se
        consulta `document.title`, que es la fuente fiable.
        """
        index = self.tabs.indexOf(view)
        if index < 0:
            return
        raw = (dom_title or "").strip() or view.title().strip()
        text = raw or host_of(view.url_string()) or "Nueva pestaña"
        self.tabs.setTabText(index, truncate(text, 26))
        self.tabs.setTabToolTip(index, raw)
        if view is self.current_view():
            self._update_window_title()

    def _refresh_title_from_document(self, view: WebView) -> None:
        if view.is_new_tab_page:
            return
        try:
            view.page().runJavaScript(
                "document.title", lambda title, v=view: self._sync_titles(v, title)
            )
        except RuntimeError:
            pass

    def _on_url_changed(self, view: WebView) -> None:
        if view is self.current_view():
            self._update_omnibox(view)
            self._update_nav_actions(view)
            self._update_star(view)
            self._update_window_title()

    def _on_icon_changed(self, view: WebView) -> None:
        index = self.tabs.indexOf(view)
        if index < 0:
            return
        icon = view.icon()
        if icon.isNull():
            icon = _letter_icon(view.title() or host_of(view.url_string()), view.url_string())
        self.tabs.setTabIcon(index, icon)

    def _on_load_started(self, view: WebView) -> None:
        if view is not self.current_view():
            return
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.action_reload.setText("✕")
        self.action_reload.setToolTip("Detener")
        self.statusBar().showMessage(f"Cargando {display_url(view.url_string())}…")

    def _on_load_progress(self, view: WebView, value: int) -> None:
        if view is self.current_view():
            self.progress.setValue(value)

    def _on_load_finished(self, view: WebView, ok: bool) -> None:
        self._sync_titles(view)
        if ok:
            self._refresh_title_from_document(view)
        if view is self.current_view():
            self.progress.setVisible(False)
            self.action_reload.setText("⟳")
            self.action_reload.setToolTip("Recargar (Ctrl+R)")
            self.statusBar().showMessage("Listo" if ok else "No se pudo cargar la página", 5000)
            self._update_nav_actions(view)
            self._update_star(view)

        if ok and not view.is_new_tab_page and not self.incognito:
            url = view.url_string()
            if is_web_url(url):
                self.history.add(view.title(), url)

    def _on_status_hint(self, message: str, _timeout: int) -> None:
        self.statusBar().showMessage(display_url(message, 90) if message else "Listo", 0 if message else 1500)

    def _on_render_terminated(self, view: WebView, status, code: int) -> None:
        if code == 0:
            return
        index = self.tabs.indexOf(view)
        name = self.tabs.tabText(index) if index >= 0 else "pestaña"
        self.statusBar().showMessage(f"El proceso de «{name}» falló (código {code})", 8000)

    def _update_window_title(self) -> None:
        view = self.current_view()
        title = view.title().strip() if view is not None else ""
        prefix = "Incógnito — " if self.incognito else ""
        self.setWindowTitle(f"{prefix}{title} · {BRAND}" if title else f"{prefix}{BRAND}")

    # -------------------------------------------------------------- omnibox
    def _update_omnibox(self, view: WebView) -> None:
        url = "" if view.is_new_tab_page else view.url_string()
        if url == "about:blank":
            url = ""
        if self.omnibox.text() == url:
            return
        self.omnibox.setText(url)
        self.omnibox.setCursorPosition(0)

    def _navigate_from_omnibox(self) -> None:
        text = self.omnibox.text().strip()
        view = self.current_view()
        if not text or view is None:
            return
        if self.open_internal_page(text):
            self.omnibox.clearFocus()
            return
        target = normalize_input(text, self.settings.search_template)
        view.load_input(target)
        view.setFocus()
        self.statusBar().showMessage(f"Cargando {display_url(target)}…")

    def open_internal_page(self, text: str) -> bool:
        """Páginas internas tipo chrome://settings, chrome://history, etc."""
        value = (text or "").strip().lower()
        prefix = next(
            (p for p in ("chrome://", "chromium://", "about:") if value.startswith(p)), None
        )
        if prefix is None:
            return False
        page = value[len(prefix):].strip("/").split("/")[0]

        if page in ("settings", "preferences", "ajustes"):
            self.show_settings()
        elif page in ("downloads", "descargas"):
            self.show_downloads()
        elif page in ("history", "historial"):
            self.show_history()
        elif page in ("bookmarks", "marcadores"):
            self.show_bookmarks_manager()
        elif page in ("newtab", "new-tab", "newtabpage", "blank", "home"):
            view = self.current_view()
            if view is not None:
                self.load_new_tab_page(view)
        elif page in ("devtools", "inspect"):
            self.open_devtools()
        else:
            self.statusBar().showMessage(
                "Páginas internas: chrome://settings, chrome://history, "
                "chrome://downloads, chrome://bookmarks, chrome://newtab, chrome://devtools",
                8000,
            )
        return True

    def _completion_chosen(self, text: str) -> None:
        self.omnibox.setText(text)
        self._navigate_from_omnibox()

    def _refresh_completions(self) -> None:
        values: list[str] = []
        for item in self.bookmarks.items():
            url = str(item.get("url", ""))
            if url and url not in values:
                values.append(url)
        for entry in self.history.entries()[:600]:
            url = str(entry.get("url", ""))
            if url and url not in values:
                values.append(url)
        self._completion_model.setStringList(values)

    # ------------------------------------------------------------ navegación
    def _update_nav_actions(self, view: WebView) -> None:
        history = view.page().history()
        self.action_back.setEnabled(history.canGoBack())
        self.action_forward.setEnabled(history.canGoForward())

    def go_back(self) -> None:
        view = self.current_view()
        if view is not None:
            view.back()

    def go_forward(self) -> None:
        view = self.current_view()
        if view is not None:
            view.forward()

    def reload_or_stop(self) -> None:
        view = self.current_view()
        if view is None:
            return
        if self.progress.isVisible():
            view.stop()
            self.progress.setVisible(False)
            self.action_reload.setText("⟳")
            self.action_reload.setToolTip("Recargar (Ctrl+R)")
        elif view.is_new_tab_page:
            self.load_new_tab_page(view)
        else:
            view.reload()

    def hard_reload(self) -> None:
        self.trigger_page_action(QWebEnginePage.WebAction.ReloadAndBypassCache)

    def stop_loading(self) -> None:
        view = self.current_view()
        if view is not None:
            view.stop()
            self.progress.setVisible(False)

    def go_home(self) -> None:
        view = self.current_view()
        if view is None:
            return
        homepage = (self.settings.get("homepage") or "").strip()
        if homepage:
            view.load_input(normalize_input(homepage, self.settings.search_template))
        else:
            self.load_new_tab_page(view)

    def trigger_page_action(self, web_action) -> None:
        page = self.current_page()
        if page is not None:
            page.triggerAction(web_action)

    def change_zoom(self, delta: float) -> None:
        view = self.current_view()
        if view is not None:
            self.set_zoom(round(view.zoom + delta, 2))

    def set_zoom(self, factor: float) -> None:
        view = self.current_view()
        if view is None:
            return
        view.set_zoom(factor)
        self.statusBar().showMessage(f"Zoom {int(view.zoom * 100)}%", 2500)

    def open_local_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo",
            str(Path.home()),
            "Páginas web (*.html *.htm *.xhtml *.svg *.pdf *.txt);;Todos los archivos (*)",
        )
        if path:
            self.new_tab(QUrl.fromLocalFile(path).toString())

    # ------------------------------------------------- buscar en la página
    def open_find_bar(self) -> None:
        self.find_bar.setVisible(True)
        self.find_input.setFocus()
        self.find_input.selectAll()
        if self.find_input.text():
            self._find_changed(self.find_input.text())

    def close_find_bar(self) -> None:
        self.find_bar.setVisible(False)
        page = self.current_page()
        if page is not None:
            page.findText("")
        self.find_count.setText("")

    def _find_changed(self, text: str) -> None:
        page = self.current_page()
        if page is None:
            return
        if not text:
            page.findText("")
            self.find_count.setText("")
            return
        page.findText(text)

    def find_next(self, backwards: bool) -> None:
        page = self.current_page()
        text = self.find_input.text()
        if page is None or not text:
            return
        if backwards:
            page.findText(text, QWebEnginePage.FindFlag.FindBackward)
        else:
            page.findText(text)

    def _on_find_finished(self, view: WebView, result) -> None:
        if view is not self.current_view():
            return
        total = result.numberOfMatches()
        active = result.activeMatch()
        self.find_count.setText(f"{active}/{total}" if total else "Sin resultados")

    # ------------------------------------------------------------ marcadores
    def _update_star(self, view: WebView) -> None:
        url = view.url_string()
        saved = bool(url) and not view.is_new_tab_page and self.bookmarks.contains(url)
        self.action_star.setText("★" if saved else "☆")
        self.action_star.setToolTip(
            "Quitar de marcadores (Ctrl+D)" if saved else "Guardar en marcadores (Ctrl+D)"
        )

    def toggle_bookmark(self) -> None:
        view = self.current_view()
        if view is None:
            return
        url = view.url_string()
        if not url or url == "about:blank" or view.is_new_tab_page:
            self.statusBar().showMessage("Esta página no se puede marcar", 3000)
            return
        added = self.bookmarks.toggle(view.title(), url)
        self._update_star(view)
        self.statusBar().showMessage("Marcador guardado" if added else "Marcador eliminado", 2500)

    def _rebuild_bookmarks_bar(self) -> None:
        self.bookmarks_bar.clear()
        items = self.bookmarks.items()
        if not items:
            label = QLabel("Sin marcadores — pulsa la estrella o Ctrl+D para guardar la página actual")
            label.setObjectName("MutedHint")
            self.bookmarks_bar.addWidget(label)
            return
        for item in items[:40]:
            url = str(item.get("url", ""))
            title = str(item.get("title", "")) or url
            button = QToolButton()
            button.setObjectName("BookmarkButton")
            button.setText(truncate(title, 22))
            button.setToolTip(f"{title}\n{url}")
            button.setIcon(_letter_icon(title or url, url))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.clicked.connect(lambda _checked=False, u=url: self.open_url(u, False))
            button.customContextMenuRequested.connect(
                lambda pos, b=button, u=url, t=title: self._bookmark_context_menu(b, u, t, pos)
            )
            self.bookmarks_bar.addWidget(button)

    def _bookmark_context_menu(self, button: QToolButton, url: str, title: str, pos) -> None:
        menu = QMenu(self)
        menu.addAction("Abrir", lambda: self.open_url(url, False))
        menu.addAction("Abrir en pestaña nueva", lambda: self.open_url(url, True))
        menu.addSeparator()
        menu.addAction("Renombrar…", lambda: self._rename_bookmark(url, title))
        menu.addAction("Eliminar", lambda: self.bookmarks.remove(url))
        menu.exec(button.mapToGlobal(pos))

    def _rename_bookmark(self, url: str, title: str) -> None:
        new_name, ok = QInputDialog.getText(self, "Renombrar marcador", "Nombre:", text=title)
        if ok and new_name.strip():
            self.bookmarks.rename(url, new_name.strip())

    def _toggle_bookmarks_bar(self, checked: bool) -> None:
        self.bookmarks_bar.setVisible(checked)
        self.settings.set("show_bookmarks_bar", checked)

    def show_bookmarks_manager(self) -> None:
        BookmarksDialog(self.bookmarks, self.open_url, self).exec()

    # -------------------------------------------------------------- historial
    def show_history(self) -> None:
        HistoryDialog(self.history, self.open_url, self).exec()

    def open_url(self, url: str, new_tab: bool = False, background: bool = False) -> None:
        if self.open_internal_page(url):
            return
        target = normalize_input(url, self.settings.search_template)
        if not target:
            return
        if new_tab:
            self.new_tab(target, focus=False, background=background, activate=not background)
            return
        view = self.current_view()
        if view is None:
            self.new_tab(target, focus=False)
        else:
            view.load_input(target)
            view.setFocus()

    # -------------------------------------------------------------- descargas
    def _on_download_started(self, download) -> None:
        self._show_download_row(download)
        self._refresh_downloads_button()
        self.statusBar().showMessage(f"Descargando {download.name}…", 4000)

    def _show_download_row(self, download) -> None:
        while self._downloads_row_layout.count():
            item = self._downloads_row_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._downloads_row_layout.addWidget(DownloadRow(download, self._downloads_row_host))
        self.downloads_bar.setVisible(True)

    def _refresh_downloads_button(self) -> None:
        active = self.downloads.active_count()
        self.action_downloads.setText(f"⭳ {active}" if active else "⭳")
        self.action_downloads.setToolTip(
            f"{active} descarga(s) en curso (Ctrl+J)" if active else "Descargas (Ctrl+J)"
        )

    def show_downloads(self) -> None:
        DownloadsDialog(self.downloads, self).exec()

    # ---------------------------------------------------------------- ajustes
    def show_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self, clear_data=self.clear_browsing_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        reload_needed = values.get("javascript") != self.settings.get("javascript") or (
            values.get("user_agent", "") != self.settings.get("user_agent", "")
        )
        self.settings.update(values)
        self.apply_settings(reload_needed=reload_needed)

    def apply_settings(self, reload_needed: bool = False) -> None:
        apply_theme(QApplication.instance(), self.settings.get("theme", "dark"))
        self.ignore_certificate_errors = bool(self.settings.get("ignore_certificate_errors"))
        self.action_show_bookmarks.setChecked(bool(self.settings.get("show_bookmarks_bar")))
        if not self.incognito:
            user_agent = self.settings.get("user_agent") or decorate_user_agent(
                self.context.default_user_agent
            )
            if user_agent:
                self.profile.setHttpUserAgent(user_agent)

        zoom = float(self.settings.get("default_zoom", 1.0))
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            if not isinstance(view, WebView):
                continue
            self._apply_page_settings(view.page())
            view.set_zoom(zoom)
            if view.is_new_tab_page:
                self.load_new_tab_page(view)
            elif reload_needed:
                view.reload()
        self._rebuild_bookmarks_bar()

    def clear_browsing_data(self) -> None:
        answer = QMessageBox.question(
            self,
            "Borrar datos de navegación",
            "Se borrarán cookies, caché e historial de este perfil.\n¿Continuar?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.history.clear()
        self.statusBar().showMessage("Datos de navegación borrados", 4000)

    # ------------------------------------------------- menús contextuales
    def _show_main_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("Nueva pestaña", self.new_tab_focused, "Ctrl+T")
        menu.addAction("Nueva ventana", lambda: self.context.open_window(), "Ctrl+N")
        menu.addAction(
            "Nueva ventana privada", lambda: self.context.open_window(incognito=True), "Ctrl+Shift+N"
        )
        menu.addSeparator()
        menu.addAction("Historial", self.show_history, "Ctrl+H")
        menu.addAction("Marcadores", self.show_bookmarks_manager, "Ctrl+Shift+O")
        menu.addAction("Descargas", self.show_downloads, "Ctrl+J")
        menu.addSeparator()
        menu.addAction("Buscar en la página…", self.open_find_bar, "Ctrl+F")
        menu.addAction("Aumentar zoom", lambda: self.change_zoom(0.1))
        menu.addAction("Reducir zoom", lambda: self.change_zoom(-0.1))
        menu.addAction("Pantalla completa", self.toggle_fullscreen, "F11")
        menu.addSeparator()
        menu.addAction("Herramientas de desarrollo", self.open_devtools, "Ctrl+Shift+I")
        menu.addAction("Ajustes", self.show_settings, "Ctrl+,")
        menu.addAction(f"Acerca de {BRAND}", self.show_about)
        menu.addSeparator()
        menu.addAction("Salir", self.close_all_windows, "Ctrl+Q")
        menu.exec(self._menu_button.mapToGlobal(self._menu_button.rect().bottomLeft()))

    def _show_tab_menu(self, pos) -> None:
        bar = self.tabs.tabBar()
        index = bar.tabAt(pos)
        menu = QMenu(self)
        if index < 0:
            menu.addAction("Nueva pestaña", self.new_tab_focused)
            menu.addAction("Reabrir pestaña cerrada", self.reopen_closed_tab)
        else:
            menu.addAction("Recargar", lambda: self._reload_tab(index))
            menu.addAction("Duplicar", lambda: self.new_tab(self._tab_url(index)))
            menu.addSeparator()
            menu.addAction("Cerrar", lambda: self.close_tab(index))
            menu.addAction("Cerrar las demás", lambda: self._close_other_tabs(index))
            menu.addAction("Cerrar las de la derecha", lambda: self._close_tabs_to_right(index))
        menu.exec(bar.mapToGlobal(pos))

    def _reload_tab(self, index: int) -> None:
        view = self.tabs.widget(index)
        if isinstance(view, WebView):
            view.reload()

    def _close_other_tabs(self, index: int) -> None:
        for position in range(self.tabs.count() - 1, -1, -1):
            if position != index:
                self.close_tab(position)

    def _close_tabs_to_right(self, index: int) -> None:
        for position in range(self.tabs.count() - 1, index, -1):
            self.close_tab(position)

    def _show_context_menu(self, view: WebView, pos) -> None:
        page = view.page()
        request = view.lastContextMenuRequest()
        menu = QMenu(self)

        history = page.history()
        back = menu.addAction("Atrás", page.back)
        back.setEnabled(history.canGoBack())
        forward = menu.addAction("Adelante", page.forward)
        forward.setEnabled(history.canGoForward())
        menu.addAction("Recargar", page.reload)

        link_url = request.linkUrl().toString() if request is not None else ""
        media_type = request.mediaType() if request is not None else None
        selected = request.selectedText() if request is not None else ""
        editable = bool(request.isContentEditable()) if request is not None else False
        flags = request.editFlags() if request is not None else None
        media_flags = request.mediaFlags() if request is not None else None
        media_url = request.mediaUrl().toString() if request is not None else ""

        if link_url:
            menu.addSeparator()
            menu.addAction("Abrir enlace en pestaña nueva", lambda: self.open_url(link_url, True))
            menu.addAction(
                "Abrir enlace en ventana privada",
                lambda: self.context.open_window(True, [link_url]),
            )
            menu.addAction(
                "Copiar dirección del enlace",
                lambda: QApplication.clipboard().setText(link_url),
            )
            if request is not None and request.linkText():
                text = request.linkText()
                menu.addAction("Copiar texto del enlace", lambda: QApplication.clipboard().setText(text))
            menu.addAction(
                "Guardar enlace como…",
                lambda: page.triggerAction(QWebEnginePage.WebAction.DownloadLinkToDisk),
            )

        if media_type == QWebEngineContextMenuRequest.MediaType.MediaTypeImage and media_url:
            menu.addSeparator()
            menu.addAction(
                "Abrir imagen en pestaña nueva", lambda: self.open_url(media_url, True)
            )
            menu.addAction(
                "Copiar imagen",
                lambda: page.triggerAction(QWebEnginePage.WebAction.CopyImageToClipboard),
            )
            if media_flags is not None and media_flags & QWebEngineContextMenuRequest.MediaFlag.MediaCanSave:
                menu.addAction(
                    "Guardar imagen como…",
                    lambda: page.triggerAction(QWebEnginePage.WebAction.DownloadImageToDisk),
                )
        elif media_type in (
            QWebEngineContextMenuRequest.MediaType.MediaTypeVideo,
            QWebEngineContextMenuRequest.MediaType.MediaTypeAudio,
        ):
            menu.addSeparator()
            menu.addAction(
                "Abrir el medio en una pestaña nueva", lambda: self.open_url(media_url, True)
            )
            if media_flags is not None and media_flags & QWebEngineContextMenuRequest.MediaFlag.MediaCanToggleControls:
                menu.addAction(
                    "Mostrar/ocultar controles",
                    lambda: page.triggerAction(QWebEnginePage.WebAction.ToggleMediaControls),
                )

        if editable and flags is not None:
            menu.addSeparator()
            cut = menu.addAction("Cortar", lambda: page.triggerAction(QWebEnginePage.WebAction.Cut))
            cut.setEnabled(bool(flags & QWebEngineContextMenuRequest.EditFlag.CanCut))
            copy = menu.addAction("Copiar", lambda: page.triggerAction(QWebEnginePage.WebAction.Copy))
            copy.setEnabled(bool(flags & QWebEngineContextMenuRequest.EditFlag.CanCopy))
            paste = menu.addAction("Pegar", lambda: page.triggerAction(QWebEnginePage.WebAction.Paste))
            paste.setEnabled(bool(flags & QWebEngineContextMenuRequest.EditFlag.CanPaste))
            menu.addAction(
                "Seleccionar todo",
                lambda: page.triggerAction(QWebEnginePage.WebAction.SelectAll),
            )
        elif selected:
            menu.addSeparator()
            menu.addAction(
                "Copiar",
                lambda: QApplication.clipboard().setText(selected),
            )
            menu.addAction(
                f"Buscar «{truncate(selected, 24)}» en la web",
                lambda: self.open_url(selected, True),
            )

        menu.addSeparator()
        menu.addAction("Guardar como PDF…", self.save_pdf)
        menu.addAction(
            "Código fuente", lambda: page.triggerAction(QWebEnginePage.WebAction.ViewSource)
        )
        menu.addAction(
            "Inspeccionar elemento",
            lambda: page.triggerAction(QWebEnginePage.WebAction.InspectElement),
        )
        menu.exec(view.mapToGlobal(pos))

    # ------------------------------------------------------------ herramientas
    def save_page(self) -> None:
        view = self.current_view()
        if view is None:
            return
        suggested = _suggest_filename(view.title(), "html")
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar página", str(self.settings.download_path / suggested), "HTML (*.html)"
        )
        if not path:
            return
        ok = view.page().save(
            path, QWebEngineDownloadRequest.SavePageFormat.CompleteHtmlSaveFormat
        )
        self.statusBar().showMessage(
            "Página guardada" if ok else "No se pudo guardar la página", 4000
        )

    def save_pdf(self) -> None:
        view = self.current_view()
        if view is None:
            return
        suggested = _suggest_filename(view.title(), "pdf")
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como PDF", str(self.settings.download_path / suggested), "PDF (*.pdf)"
        )
        if path:
            view.page().printToPdf(path)
            self.statusBar().showMessage("Generando PDF…")

    def _on_pdf_finished(self, file_path: str, success: bool) -> None:
        self.statusBar().showMessage(
            f"PDF guardado en {file_path}" if success else "No se pudo generar el PDF", 6000
        )

    def print_page(self) -> None:
        view = self.current_view()
        if view is None:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Imprimir")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            view.print(printer)

    def open_devtools(self) -> None:
        page = self.current_page()
        if page is None:
            return
        if self._devtools_view is None:
            self._devtools_view = QWebEngineView()
            self._devtools_page = QWebEnginePage(self.profile, self._devtools_view)
            self._devtools_view.setPage(self._devtools_page)
            self._devtools_view.setWindowTitle(f"Herramientas de desarrollo — {BRAND}")
            self._devtools_view.setWindowIcon(brand_icon(48))
            self._devtools_view.resize(1024, 660)
        try:
            self._devtools_page.setInspectedPage(page)
        except RuntimeError as error:
            self.statusBar().showMessage(f"No se pudo abrir DevTools: {error}", 6000)
            return
        self._devtools_view.show()
        self._devtools_view.raise_()
        self._devtools_view.activateWindow()

    def _sync_devtools(self) -> None:
        if self._devtools_view is None or not self._devtools_view.isVisible():
            return
        page = self.current_page()
        if page is None:
            return
        try:
            self._devtools_page.setInspectedPage(page)
        except (RuntimeError, AttributeError):
            pass

    # ------------------------------------------ permisos y certificados
    def _on_permission_requested(self, permission) -> None:
        try:
            if not permission.isValid():
                return
            origin = permission.origin().toString()
            label = _PERMISSION_LABELS.get(permission.permissionType(), "un recurso protegido")
        except RuntimeError:
            return

        answer = QMessageBox.question(
            self, "Permiso del sitio", f"¿Permitir que {origin} use {label}?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            permission.grant()
        else:
            permission.deny()

    def notify_certificate_error(self, error) -> None:
        url = error.url().toString()
        if url in self._cert_warned:
            return
        self._cert_warned.add(url)
        description = error.description() if hasattr(error, "description") else ""
        QMessageBox.warning(
            self,
            "Certificado no válido",
            f"La conexión con:\n\n{url}\n\n"
            "no es segura porque su certificado no se pudo verificar.\n"
            f"{description}",
        )

    def _on_authentication_required(self, request_url: QUrl, authenticator) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Autenticación requerida")
        layout = QVBoxLayout(dialog)
        layout.setSpacing(8)

        layout.addWidget(
            QLabel(
                f"El servidor <b>{request_url.host()}</b> solicita credenciales"
                + (f" para el área «{authenticator.realm()}»." if authenticator.realm() else ".")
            )
        )
        layout.addWidget(QLabel("Usuario"))
        user = QLineEdit(authenticator.user())
        layout.addWidget(user)
        layout.addWidget(QLabel("Contraseña"))
        password = QLineEdit(authenticator.password())
        password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(dialog.reject)
        accept = QPushButton("Entrar")
        accept.setDefault(True)
        accept.clicked.connect(dialog.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(accept)
        layout.addLayout(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            authenticator.setUser(user.text())
            authenticator.setPassword(password.text())

    # --------------------------------------------------- pantalla completa
    def _on_fullscreen_requested(self, request) -> None:
        request.accept()
        if request.toggleOn():
            self._html_fullscreen = True
            self._set_chrome_visible(False)
            self.showFullScreen()
        else:
            self._leave_html_fullscreen()

    def _leave_html_fullscreen(self) -> None:
        self._html_fullscreen = False
        self.showNormal()
        self._set_chrome_visible(True)

    def _set_chrome_visible(self, visible: bool) -> None:
        self.toolbar.setVisible(visible)
        self.menuBar().setVisible(visible)
        self.statusBar().setVisible(visible)
        self.bookmarks_bar.setVisible(
            visible and bool(self.settings.get("show_bookmarks_bar"))
        )

    def toggle_fullscreen(self) -> None:
        if self._html_fullscreen:
            self._leave_html_fullscreen()
            return
        if self.isFullScreen():
            self.showNormal()
            self._set_chrome_visible(True)
        else:
            self._set_chrome_visible(False)
            self.showFullScreen()

    def show_about(self) -> None:
        info = {
            "Versión": "1.0",
            "Motor": f"Chromium {self.context.chromium_version} (Qt WebEngine)",
            "Perfil": "incógnito (no se guarda nada)" if self.incognito else str(config_dir()),
            "Descargas": str(self.settings.download_path),
        }
        AboutDialog(info, self).exec()

    # ------------------------------------------------------- ciclo de vida
    def close_all_windows(self) -> None:
        for window in list(self.context.windows):
            window.close()

    def _save_session(self) -> None:
        if self.incognito:
            return
        tabs = [{"url": self._tab_url(index)} for index in range(self.tabs.count())]
        self.context.session.save(
            tabs=tabs,
            active=self.tabs.currentIndex(),
            geometry=bytes(self.saveGeometry()),
            maximized=self.isMaximized(),
        )

    def closeEvent(self, event) -> None:  # noqa: N802 (API de Qt)
        if not self.incognito:
            self._save_session()
        if self._devtools_view is not None:
            self._devtools_view.close()
        self.context.forget_window(self)
        super().closeEvent(event)
        if not self.context.windows:
            QApplication.instance().quit()

    # -------------------------------------------------- filtro de eventos
    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        omnibox = getattr(self, "omnibox", None)
        find_input = getattr(self, "find_input", None)
        tabs = getattr(self, "tabs", None)

        if omnibox is not None and obj is omnibox:
            if event.type() == QEvent.Type.FocusIn:
                self._refresh_completions()
                self.omnibox.selectAll()
            elif event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
                view = self.current_view()
                self.omnibox.clearFocus()
                if view is not None:
                    view.setFocus()
                return True
        elif find_input is not None and obj is find_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.close_find_bar()
                return True
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.find_next(bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
                return True
        elif tabs is not None and obj is tabs.tabBar() and event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.MiddleButton:
                index = tabs.tabBar().tabAt(event.position().toPoint())
                if index >= 0:
                    self.close_tab(index)
                    return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (API de Qt)
        """Escape sale de la pantalla completa (respaldo de Chromium)."""
        if event.key() == Qt.Key.Key_Escape and self._html_fullscreen:
            page = self.current_page()
            if page is not None:
                page.triggerAction(QWebEnginePage.WebAction.ExitFullScreen)
            self._leave_html_fullscreen()
            return
        super().keyPressEvent(event)


def _suggest_filename(title: str, extension: str) -> str:
    """Nombre de archivo razonable a partir del título de la página."""
    clean = "".join(
        char if char.isalnum() or char in " -_." else "_" for char in (title or "pagina")
    )
    clean = " ".join(clean.split())[:60].strip() or "pagina"
    return f"{clean}.{extension}"


def apply_theme(app: QApplication, theme: str) -> None:
    """Aplica la hoja de estilo a toda la aplicación."""
    from .theme import stylesheet

    app.setStyleSheet(stylesheet(theme))
    app.setProperty("pedrozilla_theme", theme)
