"""Ventana del navegador: pestañas, barra de direcciones, menús y todo el pegamento."""

from __future__ import annotations

import shutil
import sys
import time
from urllib.parse import quote
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    QStandardPaths,
    QStringListModel,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import (
    QWebEngineContextMenuRequest,
    QWebEngineDownloadRequest,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
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
    QSplitter,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .reader import picture_in_picture_script, reader_script
from .downloads import DownloadRow, DownloadsDialog, DownloadsManager
from .extensions import ExtensionBridge, ExtensionsDialog, extension_manager
from .icons import menu_icon
from .newtab import new_tab_html
from .newtab_bridge import NewTabBridge
from .storage import (
    SEARCH_ENGINES,
    Bookmarks,
    History,
    Session,
    Settings,
    Shortcuts,
    config_dir,
    data_dir,
)
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

# Colores de los grupos de pestañas. Se usan círculos de color en el título de
# la pestaña: QTabBar no permite teñir el fondo de una pestaña concreta de forma
# fiable con stylesheet, pero este indicador es visible en todos los temas.
GROUP_DOTS = {
    "rojo": "🔴",
    "naranja": "🟠",
    "amarillo": "🟡",
    "verde": "🟢",
    "azul": "🔵",
    "morado": "🟣",
}

# Icono real del proyecto (un .ico de varios tamaños). Si falta, se dibuja uno.
_ICON_FILE = Path(__file__).with_name("pedrozilla.ico")

_PERMISSION_LABELS = {}
try:
    from PySide6.QtWebEngineCore import QWebEnginePermission

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
except Exception:
    _PERMISSION_LABELS = {}


@lru_cache(maxsize=8)
def brand_icon(size: int = 64) -> QIcon:
    """Icono del navegador: el archivo `pedrozilla.ico` si existe.

    `size` solo se usa en la reserva dibujada de abajo; el .ico trae varios
    tamaños, así que Qt escala el que más convenga.
    """
    if _ICON_FILE.exists():
        icon = QIcon(str(_ICON_FILE))
        if not icon.isNull():
            return icon

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


def close_icon_path() -> str:
    """Ruta del icono «X» de las pestañas, dibujado una sola vez.

    Se guarda en la carpeta de configuración (no en el repositorio) y se
    inyecta en la hoja de estilo como `url(...)`. El gris elegido se ve bien
    tanto sobre pestañas claras (tema clásico) como oscuras.
    """
    path = config_dir() / "close.png"
    if not path.exists():
        pixmap = QPixmap(12, 12)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#7a7a7a"))
        pen.setWidthF(1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(3, 3, 9, 9)
        painter.drawLine(9, 3, 3, 9)
        painter.end()
        pixmap.save(str(path), "PNG")
    return str(path)


def _letter_icon(text: str, color_source: str = "", size: int = 20) -> QIcon:
    """Icono de reserva; se cachea por letra/color/tamaño.

    Antes se redibujaba cada vez que una pestaña cambiaba de favicon, aunque
    el resultado (la inicial y el color del sitio) fuese el mismo.
    """
    return _draw_letter_icon(initial_letter(text), color_for(color_source or text), size)


@lru_cache(maxsize=256)
def _draw_letter_icon(letter: str, color: str, size: int) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.setPen(QColor("#202124"))
    font = QFont()
    font.setPixelSize(max(9, int(size * 0.55)))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
    painter.end()
    return QIcon(pixmap)


class SplitView(QWidget):
    """Dos vistas web independientes dentro de una misma pestaña.

    Cada vista conserva su propio QWebEnginePage. Nunca se reutiliza una misma
    instancia de QWebEngineView en dos contenedores.
    """

    def __init__(self, views: list[WebView], parent=None) -> None:
        super().__init__(parent)
        self.views = views
        self._pinned = False
        self._group_id: str | None = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)
        for view in views:
            self.splitter.addWidget(view)
        self.splitter.setSizes([600, 600])
        layout.addWidget(self.splitter)
        for view in views:
            view.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 (API de Qt)
        if event.type() == QEvent.Type.FocusIn and obj in self.views:
            parent = self.parent()
            while parent is not None and not isinstance(parent, BrowserWindow):
                parent = parent.parent()
            if parent is not None:
                parent._active_view = obj
        return super().eventFilter(obj, event)


class BrowserContext:
    """Estado compartido: ajustes, historial, marcadores, perfiles y ventanas."""

    def __init__(self, settings: Settings, history: History, bookmarks: Bookmarks) -> None:
        self.settings = settings
        self.history = history
        self.bookmarks = bookmarks
        self.shortcuts = Shortcuts()
        self.downloads = DownloadsManager(settings)
        self.session = Session()
        self.windows: list[BrowserWindow] = []
        self.closed_tabs: list[dict[str, str]] = []
        self.default_user_agent = ""
        self.chromium_version = "desconocida"
        self.persistent_profile: QWebEngineProfile | None = None
        # Puente de extensiones (gestor Qt + estado activo persistido).
        self.extensions: ExtensionBridge | None = None
        self._attached_profiles: set[int] = set()
        self._profiles: list[QWebEngineProfile] = []

    # -- perfiles -----------------------------------------------------------
    def build_persistent_profile(self) -> QWebEngineProfile:
        from PySide6.QtWebEngineCore import QWebEngineProfile

        data_root = data_dir()
        # Qt 6.12 (comprobado empíricamente): llamar a setPersistentStoragePath()
        # con una ruta DISTINTA de la que Qt calcula por defecto deja el gestor de
        # extensiones incoherente — setExtensionEnabled() muere con un access
        # violation y installExtension() no persiste (la extensión aparece como
        # "cargada en temporal" sin estar instalada). Por eso NO se sobrescribe la
        # ruta de almacenamiento: la de Qt, fijada con org/app = Pedrozilla
        # (main.py), cae dentro de %APPDATA%\Pedrozilla\... (carpeta nuestra) y es
        # la única con la que el gestor de extensiones funciona. La caché no
        # participa en ese sistema y sí se redirige a LOCALAPPDATA (verificado).
        default_profile = QWebEngineProfile.defaultProfile()
        default_profile.setCachePath(str(data_root / "default-cache"))
        self.default_user_agent = default_profile.httpUserAgent()
        self.chromium_version = self._chromium_from_ua(self.default_user_agent)

        # Ruta por defecto que usará Qt para nuestro perfil con nombre:
        # AppDataLocation/QtWebEngine/<storageName>. Es la misma que reporta
        # QWebEngineProfile.persistentStoragePath() sin override (comprobado:
        # coincide con installPath() del gestor de extensiones). Se calcula sin
        # crear un perfil temporal, porque abrir uno dejaría archivos en la ruta
        # destino y bloquearía la migración posterior.
        destino = (
            Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
            / "QtWebEngine"
            / "pedrozilla"
        )

        # Migración única: los builds antiguos guardaban el perfil con datos del
        # usuario (cookies, sesiones) en LOCALAPPDATA\pedrozilla\profile; se
        # traslada a la ubicación nueva cuando esta aún no contiene datos (si el
        # destino ya tiene un perfil real, jamás se pisa). Cookies/History marcan
        # un perfil "con datos"; un destino sin ellos es andamiaje (p. ej. de
        # pruebas) y se reemplaza. Solo en producción (org/app fijados): los
        # scripts de prueba no fijan org/app y no deben arrastrar los datos
        # reales a su ruta por defecto de desarrollo.
        origen = data_root / "profile"
        origen_datos = (origen / "Cookies").exists() or (origen / "History").exists()
        destino_datos = (destino / "Cookies").exists() or (destino / "History").exists()
        if (
            QCoreApplication.organizationName()
            and QCoreApplication.applicationName()
            and origen_datos
            and not destino_datos
        ):
            try:
                if destino.exists():
                    shutil.rmtree(destino)  # andamiaje sin datos reales
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(origen), str(destino))
            except OSError as exc:
                # Nunca se bloquea el arranque: se continúa con perfil nuevo,
                # pero se deja constancia del fallo para poder diagnosticarlo.
                print(f"[pedrozilla] no se pudo migrar el perfil antiguo: {exc}", file=sys.stderr)

        profile = QWebEngineProfile("pedrozilla", QApplication.instance())
        profile.setCachePath(str(data_root / "cache"))
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        profile.setHttpCacheMaximumSize(200 * 1024 * 1024)
        self.persistent_profile = profile
        self.configure_profile(default_profile)
        self.configure_profile(profile)

        # Extensiones Chromium (MV3): el puente restaura las que el usuario
        # tenía activas; si el perfil no las soporta (o no hay), queda en None.
        manager = extension_manager(profile)
        if manager is not None:
            self.extensions = ExtensionBridge(manager, self.settings)
            self.extensions.restore()
        return profile

    @staticmethod
    def _chromium_from_ua(user_agent: str) -> str:
        for token in (user_agent or "").split():
            if token.startswith("Chrome/"):
                return token.split("/", 1)[1]
        return "desconocida"

    @staticmethod
    def _referrer_script_source() -> str:
        return r"""
(function(){
  var policy = "__PZ_REFERRER__";
  function apply(){
    if (!document.head || document.querySelector('meta[name="referrer"]')) return;
    var meta = document.createElement("meta");
    meta.name = "referrer";
    meta.content = policy;
    document.head.appendChild(meta);
  }
  if (document.head) { apply(); return; }
  var observer = new MutationObserver(function(){
    if (document.head) { observer.disconnect(); apply(); }
  });
  observer.observe(document, {childList:true, subtree:true});
})()
"""

    def build_referrer_script(self) -> QWebEngineScript:
        valid = {
            "no-referrer",
            "same-origin",
            "strict-origin",
            "strict-origin-when-cross-origin",
        }
        policy = self.settings.get("privacy_referrer_policy", "strict-origin-when-cross-origin")
        if policy not in valid:
            policy = "strict-origin-when-cross-origin"
        script = QWebEngineScript()
        script.setName("pedrozilla-referrer")
        script.setSourceCode(self._referrer_script_source().replace("__PZ_REFERRER__", policy))
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        script.setRunsOnSubFrames(True)
        return script

    def _install_referrer_script(self, profile: QWebEngineProfile) -> None:
        scripts = profile.scripts()
        for script in list(scripts.toList()):
            if script.name() == "pedrozilla-referrer":
                scripts.remove(script)
        scripts.insert(self.build_referrer_script())

    def apply_privacy_scripts(self) -> None:
        """Vuelve a inyectar la política de referrer en todos los perfiles."""
        for profile in self._profiles:
            try:
                self._install_referrer_script(profile)
            except RuntimeError:
                continue

    def configure_profile(self, profile: QWebEngineProfile) -> None:
        user_agent = self.settings.get("user_agent") or decorate_user_agent(self.default_user_agent)
        if user_agent:
            profile.setHttpUserAgent(user_agent)
        if not any(existing is profile for existing in self._profiles):
            self._profiles.append(profile)
        self._install_referrer_script(profile)
        if id(profile) not in self._attached_profiles:
            self.downloads.attach(profile)
            self._attached_profiles.add(id(profile))

    def new_off_the_record_profile(self) -> QWebEngineProfile:
        """Perfil sin nombre: no guarda cookies, caché ni historial."""
        profile = QWebEngineProfile(QApplication.instance())
        self.configure_profile(profile)
        return profile

    # -- ventanas -----------------------------------------------------------
    def open_window(
        self,
        incognito: bool = False,
        urls: list[str] | None = None,
        debug: bool = False,
    ) -> "BrowserWindow":
        profile = self.new_off_the_record_profile() if incognito else self.persistent_profile
        first_normal_window = not incognito and not any(
            not existing.incognito for existing in self.windows
        )
        window = BrowserWindow(self, profile, incognito=incognito)
        # Debe aplicarse antes de crear las pestañas iniciales: `_wire_view` lee
        # este valor al conectar cada página.
        window.debug_console = bool(debug)
        window.open_initial_tabs(list(urls or []))
        self.windows.append(window)
        if first_normal_window:
            window.schedule_auto_update_check()
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
        # Marcador pedido por el usuario mientras la pestaña aún cargaba.
        self._pending_bookmark: WebView | None = None
        # Las sugerencias del autocompletado se reconstruyen solo al enfocar
        # la omnibox, no en cada navegación (el historial cambia muy a menudo).
        self._completions_dirty = True
        self._update_checker = None
        self._update_check_silent = True

        # Las QAction de la antigua barra de menús se conservan como objetos
        # reales (atajos y conexiones intactos) pero sus menús no se muestran.
        self._legacy_actions: dict[tuple[str, str], QAction] = {}
        self._legacy_menus: dict[str, QMenu] = {}

        self._active_view: WebView | None = None
        self._devtools_view: QWebEngineView | None = None
        self._devtools_page: QWebEnginePage | None = None
        self._html_fullscreen = False
        self._cert_warned: set[str] = set()
        self._cert_errors: dict[str, str] = {}
        self.tab_groups: dict[str, dict] = (
            {} if incognito else dict(self.context.session.data.get("groups", {}))
        )
        self.workspaces: dict[str, dict] = (
            {} if incognito else dict(self.settings.get("workspaces", {}))
        )
        self.active_workspace = str(self.settings.get("active_workspace", "personal"))
        if not self.workspaces:
            self.workspaces[self.active_workspace] = {
                "name": "Personal",
                "color": "azul",
                "tabs": [],
                "groups": {},
                "active": 0,
            }

        self.setWindowIcon(brand_icon())
        self.resize(1280, 840)
        self.setMinimumSize(600, 420)

        self._build_toolbar()
        self._build_bookmarks_bar()
        self._build_central()
        self._build_menus()
        self._build_shortcuts()
        self._build_status_bar()

        self.bookmarks.changed.connect(self._rebuild_bookmarks_bar)
        self.bookmarks.changed.connect(self._invalidate_completions)
        self.history.changed.connect(self._invalidate_completions)
        self.downloads.started.connect(self._on_download_started)
        self.downloads.updated.connect(lambda _download: self._refresh_downloads_button())

    # --------------------------------------------------------------- montaje
    def _build_central(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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

        # Estilo Firefox 7: la barra de pestañas vive fuera del QTabWidget,
        # en su propia franja encima de la barra de navegación.
        self.tab_strip = QWidget()
        self.tab_strip.setObjectName("TabStrip")
        strip_layout = QHBoxLayout(self.tab_strip)
        strip_layout.setContentsMargins(0, 0, 0, 0)
        strip_layout.setSpacing(0)
        # Que la barra ocupe solo lo que necesitan las pestañas: así el "+" queda
        # justo a la derecha de la última, no pegado al borde de la ventana.
        self.tabs.tabBar().setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        strip_layout.addWidget(self.tabs.tabBar())

        self.new_tab_button = QToolButton()
        self.new_tab_button.setObjectName("NewTabButton")
        self.new_tab_button.setText("+")
        self.new_tab_button.setToolTip("Nueva pestaña (Ctrl+T)")
        self.new_tab_button.setAutoRaise(True)
        self.new_tab_button.setFixedSize(34, 28)
        self.new_tab_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.new_tab_button.clicked.connect(self.new_tab_focused)
        strip_layout.addWidget(self.new_tab_button)
        strip_layout.addStretch(1)

        layout.addWidget(self.tab_strip)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.bookmarks_bar)

        layout.addWidget(self.tabs, 1)

        # En Firefox 7 la barra de búsqueda en la página aparece abajo.
        self.find_bar = self._make_find_bar()
        layout.addWidget(self.find_bar)

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

        self.action_back = self._action("◀", "Atrás (Alt+←)", self.go_back)
        self.action_forward = self._action("▶", "Adelante (Alt+→)", self.go_forward)
        self.action_reload = self._action("⟳", "Recargar (Ctrl+R)", self.reload_or_stop)
        self.action_home = self._action("⌂", "Página de inicio", self.go_home)
        for action in (self.action_back, self.action_forward, self.action_reload, self.action_home):
            self.toolbar.addWidget(self._toolbar_button(action))

        self.security_label = QLabel("🔎")
        self.security_label.setObjectName("SecurityIndicator")
        self.security_label.setToolTip("Escribe una dirección o una búsqueda")
        self.toolbar.addWidget(self.security_label)

        self.omnibox = QLineEdit()
        self.omnibox.setObjectName("Omnibox")
        self.omnibox.setPlaceholderText("Buscar o escribir una dirección")
        self.omnibox.setClearButtonEnabled(True)
        self.omnibox.setMinimumWidth(320)
        self.omnibox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.omnibox.returnPressed.connect(self._navigate_from_omnibox)
        self.omnibox.installEventFilter(self)

        self._completion_base: list[tuple[str, str]] = []
        self._completion_targets: dict[str, str] = {}
        self.omnibox.textEdited.connect(lambda _text: self._refresh_completions(force=True))
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

    @staticmethod
    def _action_key(text: str) -> str:
        return text.replace("&", "").replace("…", "").strip()

    def _register_action(self, container, text: str, action: QAction) -> None:
        """Guarda la QAction original para reutilizarla en el menú Pedrozilla."""
        section = (
            container.title().replace("&", "") if isinstance(container, QMenu) else "Atajos"
        )
        self._legacy_actions[(section, self._action_key(text))] = action

    def _menu(self, title: str) -> QMenu:
        """Menú contenedor que ya no se engancha en la QMenuBar visible."""
        clean = title.replace("&", "")
        menu = QMenu(clean, self)
        self._legacy_menus[clean] = menu
        return menu

    def _add(self, container, text: str, slot, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        container.addAction(action)
        self._register_action(container, text, action)
        return action

    def _add_page_action(self, menu, text: str, web_action, shortcut=None) -> QAction:
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(QKeySequence(shortcut) if isinstance(shortcut, str) else QKeySequence(shortcut))
        action.triggered.connect(lambda: self.trigger_page_action(web_action))
        menu.addAction(action)
        self._register_action(menu, text, action)
        return action

    def _build_menus(self) -> None:
        # La barra clásica queda vacía y oculta: las acciones viven en menús
        # propios y se reutilizan en el desplegable del botón naranja.
        self.menuBar().setNativeMenuBar(False)
        self.menuBar().setVisible(False)

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
        self._register_action(view_menu, "Barra de marcadores", self.action_show_bookmarks)
        self._add(view_menu, "Pantalla completa", self.toggle_fullscreen, "F11")
        view_menu.addSeparator()
        self._add_page_action(view_menu, "Ver código fuente", QWebEnginePage.WebAction.ViewSource, "Ctrl+U")
        self._add(view_menu, "DevTools", self.open_devtools, "Ctrl+Shift+I")
        view_menu.addSeparator()
        self._add(view_menu, "Modo lectura", self.toggle_reader_mode, "F9")
        self._add(view_menu, "Vista dividida", self.toggle_split_view, "Alt+V")
        self._add(view_menu, "Vídeo en ventana flotante (PiP)", self.toggle_picture_in_picture)

        history_menu = self._menu("&Historial")
        self._add(history_menu, "Atrás", self.go_back)
        self._add(history_menu, "Adelante", self.go_forward)
        self._add(history_menu, "Página de inicio", self.go_home)
        history_menu.addSeparator()
        self._add(history_menu, "Ver historial", self.show_history, "Ctrl+H")
        self._add(history_menu, "Reabrir pestaña cerrada", self.reopen_closed_tab, "Ctrl+Shift+T")
        self.closed_menu = QMenu("Pestañas cerradas recientemente", history_menu)
        self.closed_menu.aboutToShow.connect(self._fill_closed_menu)
        history_menu.addMenu(self.closed_menu)
        history_menu.addSeparator()
        self._add(history_menu, "Borrar datos de navegación", self.clear_browsing_data)

        bookmarks_menu = self._menu("&Marcadores")
        self._add(bookmarks_menu, "Añadir marcador", self.toggle_bookmark, "Ctrl+D")
        self._add(bookmarks_menu, "Administrar marcadores", self.show_bookmarks_manager, "Ctrl+Shift+O")
        # Misma QAction que en «Ver»: un único estado compartido en dos secciones.
        self._register_action(bookmarks_menu, "Barra de marcadores", self.action_show_bookmarks)

        spaces_menu = self._menu("&Espacios")
        spaces_menu.addMenu(self._workspace_menu())
        self._add(spaces_menu, "Nuevo espacio…", self.new_workspace)

        downloads_menu = self._menu("&Descargas")
        self._add(downloads_menu, "Abrir gestor de descargas", self.show_downloads, "Ctrl+J")
        self._add(downloads_menu, "Abrir carpeta de descargas", self.open_downloads_folder)
        settings_menu = self._menu("&Ajustes")
        self._add(settings_menu, "Ajustes", self.show_settings, "Ctrl+,")
        self._add(settings_menu, "Extensiones", self.show_extensions, "Ctrl+Shift+E")
        self._add(settings_menu, "Privacidad y seguridad", self.show_privacy)
        help_menu = self._menu("A&yuda")
        self._add(help_menu, "Buscar actualizaciones", self.check_updates)
        help_menu.addSeparator()
        self._add(help_menu, f"Acerca de {BRAND}", self.show_about, "F1")

    def _fill_closed_menu(self) -> None:
        """Se rellena al abrirlo para no copiar la lista en cada cambio de pestaña."""
        self.closed_menu.clear()
        entries = list(reversed(self.context.closed_tabs))
        if not entries:
            action = self.closed_menu.addAction("No hay pestañas cerradas")
            action.setEnabled(False)
            return
        for entry in entries:
            title = truncate(entry.get("title") or entry.get("url") or "Pestaña", 52)
            self.closed_menu.addAction(title, lambda item=entry: self.new_tab(item.get("url", "")))
        self.closed_menu.addSeparator()
        self._add(self.closed_menu, "Reabrir la última", self.reopen_closed_tab)

    def _build_shortcuts(self) -> None:
        # Las acciones de menú ya tienen atajo y siguen activas con la barra de
        # menús oculta: no se duplican aquí (Atrás, Adelante, Ctrl+Tab, F9…).
        for number in range(1, 10):
            self._add(self, f"Pestaña {number}", lambda n=number - 1: self._focus_tab(n), f"Ctrl+{number}")
        self._add(
            self,
            "Ir a la barra de direcciones",
            lambda: (self.omnibox.setFocus(), self.omnibox.selectAll()),
            "Ctrl+L, Alt+D",
        )
        self._add(self, "Recargar (F5)", self.reload_or_stop, "F5")
        self._add(self, "Fijar o desfijar pestaña", lambda: self.toggle_pin_tab(), "Alt+P")
        self._add(self, "Silenciar pestaña", lambda: self.toggle_mute_tab(), "Alt+M")
        self._add(self, "Crear grupo de pestañas", lambda: self.create_group(), "Alt+G")
        self._add(self, "Gestionar grupos", self._manage_groups, "Alt+Shift+G")
        self._add(self, "Cambiar de espacio de trabajo", self._cycle_workspace, "Alt+W")

    # ------------------------------------------------------------- pestañas
    def current_view(self) -> WebView | None:
        widget = self.tabs.currentWidget()
        if isinstance(widget, WebView):
            return widget
        if isinstance(widget, SplitView):
            active = self._active_view
            if active is not None and active in widget.views:
                return active
            return widget.views[0] if widget.views else None
        return None

    def views_in_tab(self, index: int) -> list[WebView]:
        widget = self.tabs.widget(index)
        if isinstance(widget, WebView):
            return [widget]
        if isinstance(widget, SplitView):
            return list(widget.views)
        return []

    def _tab_index_of_view(self, view: WebView) -> int:
        index = self.tabs.indexOf(view)
        if index >= 0:
            return index
        for position in range(self.tabs.count()):
            widget = self.tabs.widget(position)
            if isinstance(widget, SplitView) and view in widget.views:
                return position
        return -1

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

        if not self.incognito:
            self._restore_tab_metadata(
                self.context.session.data.get("tabs", []) if not urls else []
            )

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

        index = self.tabs.insertTab(self._pinned_count(), view, "Nueva pestaña")
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

        def wire(signal, slot) -> None:
            view._connections.append((signal, signal.connect(slot)))

        wire(view.titleChanged, lambda title, v=view: self._on_title_changed(v, title))
        wire(view.urlChanged, lambda _url, v=view: self._on_url_changed(v))
        wire(view.iconChanged, lambda _icon, v=view: self._on_icon_changed(v))
        wire(view.loadStarted, lambda v=view: self._on_load_started(v))
        wire(view.loadProgress, lambda value, v=view: self._on_load_progress(v, value))
        wire(view.loadFinished, lambda ok, v=view: self._on_load_finished(v, ok))
        wire(view.status_hint, self._on_status_hint)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        wire(view.customContextMenuRequested, lambda pos, v=view: self._show_context_menu(v, pos))

        wire(page.audioMutedChanged, lambda _muted, v=view: self._sync_titles(v))
        wire(page.permissionRequested, self._on_permission_requested)
        wire(page.fullScreenRequested, self._on_fullscreen_requested)
        wire(page.windowCloseRequested, lambda p=page: self._close_page_tab(p))
        wire(page.printRequested, self.print_page)
        wire(page.authenticationRequired, self._on_authentication_required)
        wire(page.findTextFinished, lambda result, v=view: self._on_find_finished(v, result))
        wire(page.pdfPrintingFinished, self._on_pdf_finished)
        wire(
            page.renderProcessTerminated,
            lambda status, code, v=view: self._on_render_terminated(v, status, code),
        )
        # El puente QWebChannel SOLO se crea para la página de nueva pestaña
        # (ver `_ensure_new_tab_bridge`). Las páginas web normales no lo
        # necesitan y antes pagaban el coste de un canal por pestaña abierta.

    def _ensure_new_tab_bridge(self, view: WebView) -> None:
        """Crea, una sola vez por vista, el canal que usa la nueva pestaña."""
        if getattr(view, "_pedrozilla_channel", None) is not None:
            return
        try:
            bridge = NewTabBridge(self.context, view)
            channel = QWebChannel(view.web_page)
            channel.registerObject("pedrozilla", bridge)
            view.web_page.setWebChannel(channel)
            view._pedrozilla_bridge = bridge
            view._pedrozilla_channel = channel
        except Exception:
            pass

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
        self._ensure_new_tab_bridge(view)
        html = new_tab_html(
            search_template=self.settings.search_template,
            engine_key=self.settings.get("search_engine", "duckduckgo"),
            theme=self.settings.get("theme", "modern"),
            shortcuts=self.context.shortcuts.items(),
            history=[] if self.incognito else self.context.history.entries(),
            newtab_prefs=self.settings.get("newtab_prefs", {}),
            workspaces=self.workspaces,
            active_workspace=self.active_workspace,
            accent=self.settings.get("accent", "#ff7a32"),
            brand=BRAND,
            footer=(
                "Ventana privada: no se guarda historial, cookies ni caché"
                if self.incognito
                else ""
            ),
        )
        view.load_html_page(html)

    def _pinned_count(self) -> int:
        return sum(
            1
            for index in range(self.tabs.count())
            if getattr(self.tabs.widget(index), "_pinned", False)
        )

    def _group_dot(self, group_id: str | None) -> str:
        if not group_id:
            return ""
        color = self.tab_groups.get(group_id, {}).get("color", "azul")
        return GROUP_DOTS.get(color, "🔵") + " "

    def _tab_prefix(self, view: WebView) -> str:
        prefix = self._group_dot(getattr(view, "_group_id", None))
        if getattr(view, "_loading", False):
            prefix += "◌ "
        if getattr(view, "_pinned", False):
            prefix += "📌 "
        try:
            if view.page() is not None and view.page().isAudioMuted():
                prefix += "🔇 "
        except RuntimeError:
            pass
        return prefix

    def toggle_pin_tab(self, index: int | None = None) -> None:
        """Fija o desfija la pestaña indicada (o la actual)."""
        if index is None:
            index = self.tabs.currentIndex()
        widget = self.tabs.widget(index)
        if not isinstance(widget, (WebView, SplitView)):
            return
        pinned = not getattr(widget, "_pinned", False)
        widget._pinned = pinned
        for view in self.views_in_tab(index):
            view._pinned = pinned
        if pinned and index != 0:
            self.tabs.tabBar().moveTab(index, 0)
            self.tabs.setCurrentIndex(0)
        elif not pinned:
            self.tabs.tabBar().moveTab(index, self._pinned_count())
        self._refresh_group_titles()
        self.statusBar().showMessage("Pestaña fijada" if pinned else "Pestaña desfijada", 2500)

    def toggle_mute_tab(self, index: int | None = None) -> None:
        """Silencia o reactiva el sonido de la pestaña indicada (o la actual)."""
        if index is None:
            index = self.tabs.currentIndex()
        views = self.views_in_tab(index)
        if not views:
            return
        view = self.current_view()
        if view is None or view not in views:
            view = views[0]
        page = view.page()
        page.setAudioMuted(not page.isAudioMuted())
        self._sync_titles(view)
        self.statusBar().showMessage(
            "Pestaña silenciada" if page.isAudioMuted() else "Sonido activado", 2500
        )

    # --------------------------------------------------------------- grupos
    def create_group(self, index: int | None = None) -> None:
        if index is None:
            index = self.tabs.currentIndex()
        if not self.views_in_tab(index):
            return
        name, ok = QInputDialog.getText(self, "Nuevo grupo", "Nombre del grupo:")
        if not ok or not name.strip():
            return
        names = list(GROUP_DOTS)
        color, ok = QInputDialog.getItem(
            self, "Nuevo grupo", "Color:", names, names.index("azul"), False
        )
        if not ok:
            return
        group_id = f"g{int(time.time() * 1000)}"
        self.tab_groups[group_id] = {
            "name": name.strip(),
            "color": color if color in GROUP_DOTS else "azul",
            "collapsed": False,
        }
        self._assign_group(index, group_id)
        self.statusBar().showMessage(f"Grupo «{name.strip()}» creado", 3000)

    def _assign_group(self, index: int, group_id: str | None) -> None:
        widget = self.tabs.widget(index)
        views = self.views_in_tab(index)
        if not views:
            return
        widget._group_id = group_id
        for view in views:
            view._group_id = group_id
        self._refresh_group_titles()
        self._apply_group_visibility()

    def _apply_group_visibility(self) -> None:
        bar = self.tabs.tabBar()
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            group_id = getattr(view, "_group_id", None)
            hidden = bool(group_id and self.tab_groups.get(group_id, {}).get("collapsed"))
            bar.setTabVisible(index, not hidden)

        if self.tabs.count() and not any(bar.isTabVisible(i) for i in range(self.tabs.count())):
            bar.setTabVisible(0, True)
        if not bar.isTabVisible(self.tabs.currentIndex()):
            for index in range(self.tabs.count()):
                if bar.isTabVisible(index):
                    self.tabs.setCurrentIndex(index)
                    break

    def _group_submenu(self, parent: QMenu, index: int) -> QMenu:
        view = self.tabs.widget(index)
        current = getattr(view, "_group_id", None) if isinstance(view, WebView) else None
        submenu = QMenu("Grupo", parent)
        submenu.addAction("Sin grupo", lambda: self._assign_group(index, None))
        for group_id, info in self.tab_groups.items():
            title = f"{self._group_dot(group_id)}{info.get('name', group_id)}"
            action = submenu.addAction(title, lambda gid=group_id: self._assign_group(index, gid))
            action.setCheckable(True)
            action.setChecked(group_id == current)
        submenu.addSeparator()
        submenu.addAction("Crear grupo nuevo…", lambda: self.create_group(index))
        return submenu

    def _manage_groups(self) -> None:
        menu = QMenu(self)
        if not self.tab_groups:
            action = menu.addAction("No hay grupos. Usa «Crear grupo nuevo…» en una pestaña.")
            action.setEnabled(False)
        for group_id, info in self.tab_groups.items():
            title = f"{self._group_dot(group_id)}{info.get('name', group_id)}"
            submenu = menu.addMenu(title)
            collapsed = bool(info.get("collapsed"))
            submenu.addAction(
                "Expandir grupo" if collapsed else "Contraer grupo",
                lambda gid=group_id: self._toggle_group_collapse(gid),
            )
            submenu.addAction(
                "Renombrar…", lambda gid=group_id: self._rename_group(gid)
            )
            submenu.addAction(
                "Cambiar color…", lambda gid=group_id: self._recolor_group(gid)
            )
            submenu.addSeparator()
            submenu.addAction(
                "Eliminar grupo (mantiene las pestañas)",
                lambda gid=group_id: self._delete_group(gid),
            )
        menu.exec(self._menu_button.mapToGlobal(self._menu_button.rect().bottomLeft()))

    def _toggle_group_collapse(self, group_id: str) -> None:
        info = self.tab_groups.get(group_id)
        if info is None:
            return
        info["collapsed"] = not info.get("collapsed", False)
        self._apply_group_visibility()

    def _rename_group(self, group_id: str) -> None:
        info = self.tab_groups.get(group_id)
        if info is None:
            return
        name, ok = QInputDialog.getText(
            self, "Renombrar grupo", "Nombre:", text=str(info.get("name", ""))
        )
        if ok and name.strip():
            info["name"] = name.strip()
            self._refresh_group_titles()

    def _recolor_group(self, group_id: str) -> None:
        info = self.tab_groups.get(group_id)
        if info is None:
            return
        names = list(GROUP_DOTS)
        color, ok = QInputDialog.getItem(
            self,
            "Color del grupo",
            "Color:",
            names,
            max(0, names.index(info.get("color", "azul")) if info.get("color") in names else 3),
            False,
        )
        if ok and color in GROUP_DOTS:
            info["color"] = color
            self._refresh_group_titles()

    def _delete_group(self, group_id: str) -> None:
        self.tab_groups.pop(group_id, None)
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if getattr(widget, "_group_id", None) == group_id:
                widget._group_id = None
            for view in self.views_in_tab(index):
                if getattr(view, "_group_id", None) == group_id:
                    view._group_id = None
        self._refresh_group_titles()
        self._apply_group_visibility()

    def _refresh_group_titles(self) -> None:
        for index in range(self.tabs.count()):
            view = self.tabs.widget(index)
            if isinstance(view, WebView):
                self._sync_titles(view)

    # ---------------------------------------------------- espacios de trabajo
    def _persist_workspaces(self) -> None:
        if self.incognito:
            return
        self.settings.set("workspaces", self.workspaces)
        self.settings.set("active_workspace", self.active_workspace)

    def _workspace_snapshot(self) -> dict:
        tabs = []
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            views = self.views_in_tab(index)
            entry = {"url": self._tab_url(index)}
            entry["group"] = getattr(widget, "_group_id", None)
            entry["pinned"] = bool(getattr(widget, "_pinned", False))
            if isinstance(widget, SplitView):
                entry["split_urls"] = [
                    view.url_string() for view in views if not view.is_new_tab_page
                ]
            tabs.append(entry)
        return {
            "tabs": tabs,
            "groups": dict(self.tab_groups),
            "active": self.tabs.currentIndex(),
        }

    def _save_current_workspace(self) -> None:
        if self.incognito:
            return
        self.workspaces.setdefault(
            self.active_workspace,
            {"name": self.active_workspace, "color": "azul", "tabs": [], "groups": {}, "active": 0},
        )
        self.workspaces[self.active_workspace].update(self._workspace_snapshot())

    def _load_workspace_snapshot(self, snapshot: dict) -> None:
        while self.tabs.count():
            index = self.tabs.count() - 1
            for view in self.views_in_tab(index):
                self._dispose_view(view)
            self.tabs.removeTab(index)
        self._active_view = None
        self.tab_groups = dict(snapshot.get("groups", {}))
        entries = snapshot.get("tabs", [])
        if not entries:
            self.new_tab(focus=False, activate=False)
            return

        for entry in entries:
            url = str(entry.get("url") or "")
            self.new_tab(
                url,
                focus=False,
                background=True,
                activate=False,
                load_newtab_page=not url,
            )
        self._restore_tab_metadata(entries)
        for index, entry in enumerate(entries):
            split_urls = entry.get("split_urls") or []
            if not split_urls:
                continue
            if index < self.tabs.count() and not isinstance(self.tabs.widget(index), SplitView):
                self.tabs.setCurrentIndex(index)
                self.toggle_split_view()
                container = self.tabs.widget(index)
                if isinstance(container, SplitView) and len(split_urls) > 1 and len(container.views) > 1:
                    container.views[1].load_input(split_urls[1])
        target = int(snapshot.get("active") or 0)
        self.tabs.setCurrentIndex(max(0, min(target, self.tabs.count() - 1)))
        self._on_tab_changed(self.tabs.currentIndex())

    def switch_workspace(self, key: str | None = None) -> None:
        if self.incognito:
            QMessageBox.information(
                self, "Espacios de trabajo",
                "Los espacios de trabajo no están disponibles en ventanas privadas.",
            )
            return
        if key is None or key not in self.workspaces:
            return
        if key == self.active_workspace:
            return
        self._save_current_workspace()
        self.active_workspace = key
        self._persist_workspaces()
        self._load_workspace_snapshot(self.workspaces[key])
        info = self.workspaces[key]
        dot = GROUP_DOTS.get(info.get("color", "azul"), "🔵")
        self.statusBar().showMessage(f"Espacio de trabajo: {dot} {info.get('name', key)}", 4000)
        self._update_window_title()

    def new_workspace(self) -> None:
        if self.incognito:
            return
        name, ok = QInputDialog.getText(self, "Nuevo espacio", "Nombre del espacio:")
        if not ok or not name.strip():
            return
        colors = list(GROUP_DOTS)
        color, ok = QInputDialog.getItem(
            self, "Nuevo espacio", "Color:", colors, colors.index("verde"), False
        )
        key = f"ws{int(time.time() * 1000)}"
        self.workspaces[key] = {
            "name": name.strip(),
            "color": color if color in GROUP_DOTS else "verde",
            "tabs": [],
            "groups": {},
            "active": 0,
        }
        self.switch_workspace(key)

    def rename_workspace(self, key: str) -> None:
        info = self.workspaces.get(key)
        if info is None:
            return
        name, ok = QInputDialog.getText(
            self, "Renombrar espacio", "Nombre:", text=str(info.get("name", ""))
        )
        if ok and name.strip():
            info["name"] = name.strip()
            self._persist_workspaces()
            self._update_window_title()

    def recolor_workspace(self, key: str) -> None:
        info = self.workspaces.get(key)
        if info is None:
            return
        colors = list(GROUP_DOTS)
        color, ok = QInputDialog.getItem(
            self, "Color del espacio", "Color:", colors,
            max(0, colors.index(info.get("color", "verde")) if info.get("color") in colors else 3),
            False,
        )
        if ok and color in GROUP_DOTS:
            info["color"] = color
            self._persist_workspaces()
            self._update_window_title()

    def delete_workspace(self, key: str) -> None:
        if len(self.workspaces) <= 1:
            QMessageBox.information(self, "Espacios de trabajo", "Debe quedar al menos un espacio.")
            return
        answer = QMessageBox.question(
            self, "Espacios de trabajo",
            "¿Eliminar este espacio y sus pestañas guardadas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.workspaces.pop(key, None)
        if self.active_workspace == key:
            self.active_workspace = next(iter(self.workspaces))
            self._load_workspace_snapshot(self.workspaces[self.active_workspace])
        self._persist_workspaces()
        self._update_window_title()

    def _workspace_menu(self) -> QMenu:
        menu = QMenu("Espacios de trabajo", self)
        for key, info in self.workspaces.items():
            dot = GROUP_DOTS.get(info.get("color", "verde"), "🔵")
            action = menu.addAction(
                f"{dot} {info.get('name', key)}", lambda k=key: self.switch_workspace(k)
            )
            action.setCheckable(True)
            action.setChecked(key == self.active_workspace)
        menu.addSeparator()
        menu.addAction("Nuevo espacio…", self.new_workspace)
        if self.active_workspace in self.workspaces:
            current = menu.addMenu("Espacio actual")
            current.addAction("Renombrar…", lambda: self.rename_workspace(self.active_workspace))
            current.addAction("Cambiar color…", lambda: self.recolor_workspace(self.active_workspace))
            current.addAction("Eliminar…", lambda: self.delete_workspace(self.active_workspace))
        return menu

    def _cycle_workspace(self) -> None:
        keys = list(self.workspaces)
        if len(keys) < 2:
            return
        index = keys.index(self.active_workspace) if self.active_workspace in keys else 0
        self.switch_workspace(keys[(index + 1) % len(keys)])

    # --------------------------------------------------------- vista dividida
    def _dispose_view(self, view: WebView) -> None:
        view.detach()
        view.web_page.triggerAction(QWebEnginePage.WebAction.Stop)
        view.hide()
        view.deleteLater()

    def toggle_split_view(self) -> None:
        """Divide la pestaña actual en dos vistas web independientes."""
        index = self.tabs.currentIndex()
        widget = self.tabs.widget(index)
        if index < 0 or widget is None:
            return

        if isinstance(widget, SplitView):
            keep = self._active_view if self._active_view in widget.views else widget.views[0]
            for view in widget.views:
                if view is not keep:
                    self._dispose_view(view)
            keep._pinned = bool(getattr(widget, "_pinned", False))
            keep._group_id = getattr(widget, "_group_id", None)
            label = self.tabs.tabText(index).replace("◫ ", "", 1)
            tooltip = self.tabs.tabToolTip(index)
            self.tabs.removeTab(index)
            self.tabs.insertTab(index, keep, label)
            self.tabs.setTabToolTip(index, tooltip)
            self.tabs.setCurrentIndex(index)
            self._active_view = keep
            self._sync_titles(keep)
            self.statusBar().showMessage("Vista dividida desactivada", 2500)
            return

        if not isinstance(widget, WebView):
            return
        right = WebView(self.profile, window=self)
        self._wire_view(right)
        right.set_zoom(float(self.settings.get("default_zoom", 1.0)))
        container = SplitView([widget, right], self.tabs)
        container._pinned = bool(getattr(widget, "_pinned", False))
        container._group_id = getattr(widget, "_group_id", None)
        label = "◫ " + self.tabs.tabText(index)
        tooltip = self.tabs.tabToolTip(index)
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, container, label)
        self.tabs.setTabToolTip(index, tooltip)
        self.tabs.setCurrentIndex(index)
        self._active_view = right
        self.load_new_tab_page(right)
        right.setFocus()
        self.statusBar().showMessage("Vista dividida: dos páginas independientes", 3000)

    def _swap_split_views(self) -> None:
        widget = self.tabs.widget(self.tabs.currentIndex())
        if not isinstance(widget, SplitView) or len(widget.views) != 2:
            return
        left, right = widget.views
        widget.splitter.insertWidget(0, right)
        widget.views = [right, left]
        self._active_view = right
        self.statusBar().showMessage("Vistas intercambiadas", 2000)

    def _close_split_side(self) -> None:
        """Cierra la vista con foco y deja la otra como pestaña normal."""
        widget = self.tabs.widget(self.tabs.currentIndex())
        if not isinstance(widget, SplitView) or len(widget.views) != 2:
            return
        keep = self._active_view if self._active_view in widget.views else widget.views[0]
        drop = widget.views[1] if keep is widget.views[0] else widget.views[0]
        self._dispose_view(drop)
        widget.views.remove(drop)
        self.toggle_split_view()

    def _restore_tab_metadata(self, entries: list[dict]) -> None:
        for index, entry in enumerate(entries[: self.tabs.count()]):
            view = self.tabs.widget(index)
            if not isinstance(view, WebView):
                continue
            group_id = entry.get("group")
            if group_id in self.tab_groups:
                view._group_id = group_id
            view._pinned = bool(entry.get("pinned"))
            if entry.get("muted"):
                view.web_page.setAudioMuted(True)
            self._sync_titles(view)
        self._apply_group_visibility()

    def close_tab(self, index: int) -> None:
        if index < 0 or index >= self.tabs.count():
            return
        widget = self.tabs.widget(index)
        if getattr(widget, "_pinned", False):
            self.statusBar().showMessage("Desfija la pestaña antes de cerrarla", 3000)
            return
        views = self.views_in_tab(index)
        view = views[0] if views else None
        if isinstance(view, WebView) and not view.is_new_tab_page:
            url = view.url_string()
            if is_web_url(url):
                self.context.closed_tabs.append({"url": url, "title": view.title()})
                del self.context.closed_tabs[:-20]

        self.tabs.removeTab(index)
        # Cortamos los callbacks y la carga antes de soltar cada vista: así un
        # tab que se cierra deja de consumir CPU de inmediato en lugar de
        # esperar a que Qt procese el deleteLater.
        for view in views:
            self._dispose_view(view)
        if self._active_view in views:
            self._active_view = None

        if self.tabs.count() == 0:
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
        views = self.views_in_tab(index)
        for view in views:
            if not view.is_new_tab_page:
                url = view.url_string()
                if url and url != "about:blank":
                    return url
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
        index = self._tab_index_of_view(view)
        if index < 0:
            return
        raw = (dom_title or "").strip() or view.title().strip()
        text = raw or host_of(view.url_string()) or "Nueva pestaña"
        self.tabs.setTabText(index, self._tab_prefix(view) + truncate(text, 26))
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
            # Los botones atrás/adelante se refrescan al terminar la carga
            # (QWebEngineHistory.canGoBack() es caro y urlChanged puede
            # dispararse varias veces por redirección).
            self._update_star(view)
            self._update_window_title()

    def _on_icon_changed(self, view: WebView) -> None:
        index = self._tab_index_of_view(view)
        if index < 0:
            return
        icon = view.icon()
        if icon.isNull():
            icon = _letter_icon(view.title() or host_of(view.url_string()), view.url_string())
        self.tabs.setTabIcon(index, icon)

    def _on_load_started(self, view: WebView) -> None:
        view._loading = True
        self._sync_titles(view)
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
        view._loading = False
        self._sync_titles(view)
        if ok:
            # document.title solo hace falta si Qt aún no tiene un título real
            # (la URL como título provisional). Evita un viaje JS por carga.
            current = view.title().strip()
            if not current or current == view.url_string():
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

        # Marcador pedido por el usuario mientras cargaba: ahora sí, con la
        # URL y el título definitivos (las redirecciones ya no lo rompen).
        if getattr(self, "_pending_bookmark", None) is view:
            self._pending_bookmark = None
            if ok:
                self._apply_bookmark_toggle(view)

    def _on_status_hint(self, message: str, _timeout: int) -> None:
        self.statusBar().showMessage(display_url(message, 90) if message else "Listo", 0 if message else 1500)

    def _on_render_terminated(self, view: WebView, status, code: int) -> None:
        if code == 0:
            return
        index = self._tab_index_of_view(view)
        name = self.tabs.tabText(index) if index >= 0 else "pestaña"
        self.statusBar().showMessage(f"El proceso de «{name}» falló (código {code})", 8000)

    def _update_window_title(self) -> None:
        view = self.current_view()
        title = view.title().strip() if view is not None else ""
        prefix = "Incógnito — " if self.incognito else ""
        info = self.workspaces.get(self.active_workspace) if hasattr(self, "workspaces") else None
        if info is not None and len(self.workspaces) > 1:
            dot = GROUP_DOTS.get(info.get("color", "verde"), "🔵")
            prefix = f"{dot} {info.get('name', self.active_workspace)} — {prefix}"
        self.setWindowTitle(f"{prefix}{title} · {BRAND}" if title else f"{prefix}{BRAND}")

    # -------------------------------------------------------------- omnibox
    def _update_omnibox(self, view: WebView) -> None:
        url = "" if view.is_new_tab_page else view.url_string()
        if url == "about:blank":
            url = ""
        if url.startswith("https://"):
            self.security_label.setText("🔒")
            self.security_label.setToolTip("Conexión segura (HTTPS)")
        elif url.startswith("http://"):
            self.security_label.setText("⚠")
            self.security_label.setToolTip("Conexión sin cifrar (HTTP)")
        else:
            self.security_label.setText("🔎")
            self.security_label.setToolTip("Escribe una dirección o una búsqueda")
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
        elif page in ("reader", "lectura"):
            self.toggle_reader_mode()
        elif page in ("pip", "picture-in-picture"):
            self.toggle_picture_in_picture()
        elif page in ("privacy", "privacidad"):
            self.show_privacy()
        else:
            self.statusBar().showMessage(
                "Páginas internas: chrome://settings, chrome://history, "
                "chrome://downloads, chrome://bookmarks, chrome://newtab, "
                "chrome://devtools, chrome://reader, chrome://privacy",
                8000,
            )
        return True

    def _completion_chosen(self, text: str) -> None:
        target = self._completion_targets.get(text, text)
        self.omnibox.setText(target)
        self._navigate_from_omnibox()

    def _invalidate_completions(self) -> None:
        self._completions_dirty = True

    def _refresh_completions(self, force: bool = False) -> None:
        """Construye sugerencias con icono de tipo y destino real.

        La lista base (marcadores + historial) solo se reconstruye cuando el
        historial o los marcadores cambian. Al escribir se reutiliza y solo se
        añade la sugerencia de búsqueda del motor activo.
        """
        if self._completions_dirty:
            base: list[tuple[str, str]] = []
            seen: set[str] = set()
            for item in self.bookmarks.items():
                url = str(item.get("url", ""))
                if url and url not in seen:
                    seen.add(url)
                    title = str(item.get("title", "") or display_url(url))
                    base.append((f"⭐ {title} — {display_url(url)}", url))
            for entry in self.history.entries()[:600]:
                url = str(entry.get("url", ""))
                if url and url not in seen:
                    seen.add(url)
                    title = str(entry.get("title", "") or display_url(url))
                    base.append((f"🕘 {title} — {display_url(url)}", url))
            self._completion_base = base
            self._completions_dirty = False

        values = [display for display, _url in self._completion_base]
        targets = {display: url for display, url in self._completion_base}

        query = self.omnibox.text().strip()
        if query and len(query) >= 2 and not is_web_url(query):
            engine_key = self.settings.get("search_engine", "duckduckgo")
            label, template = SEARCH_ENGINES.get(
                engine_key, SEARCH_ENGINES["duckduckgo"]
            )
            display = f"🔎 Buscar en {label}: {query}"
            values.insert(0, display)
            targets[display] = template.replace("{query}", quote(query))

        self._completion_targets = targets
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
        # Si la página aún carga, esperamos al final: las redirecciones cambian
        # la URL y el título, y guardar antes deja marcadores "rotos"
        # (la estrella se vacía nada más cargar).
        if view.is_loading:
            self._pending_bookmark = view
            self.statusBar().showMessage("Guardando el marcador al terminar de cargar…", 3500)
            return
        self._apply_bookmark_toggle(view)

    def _apply_bookmark_toggle(self, view: WebView) -> None:
        """Guarda/quita el marcador con la URL y el título definitivos."""
        url = view.url_string()
        title = view.title().strip() or host_of(url) or url
        added = self.bookmarks.toggle(title, url)
        self._update_star(view)
        self.statusBar().showMessage(
            "Marcador guardado" if added else "Marcador eliminado", 2500
        )

    def _rebuild_bookmarks_bar(self) -> None:
        # Si el usuario ocultó la barra no merece la pena crear 40 botones
        # (se reconstruye al volver a mostrarla).
        if self.bookmarks_bar.isHidden():
            return
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
        if checked:
            self._rebuild_bookmarks_bar()

    def show_bookmarks_manager(self) -> None:
        # Los diálogos se importan al abrirlos: no hacen falta para arrancar.
        from .dialogs import BookmarksDialog

        BookmarksDialog(self.bookmarks, self.open_url, self).exec()

    # -------------------------------------------------------------- historial
    def show_history(self) -> None:
        from .dialogs import HistoryDialog

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

    def open_downloads_folder(self) -> None:
        """Abre la carpeta de descargas con la aplicación del sistema."""
        folder = self.settings.download_path
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    # ---------------------------------------------------------------- ajustes
    def show_settings(self) -> None:
        from .dialogs import SettingsDialog

        dialog = SettingsDialog(self.settings, self, clear_data=self.clear_browsing_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        reload_needed = values.get("javascript") != self.settings.get("javascript") or (
            values.get("user_agent", "") != self.settings.get("user_agent", "")
        )
        self.settings.update(values)
        self.apply_settings(reload_needed=reload_needed)

    def show_extensions(self) -> None:
        """Abre el gestor de extensiones (solo perfiles persistentes)."""
        if self.context.extensions is None:
            QMessageBox.information(
                self,
                "Extensiones",
                "Las extensiones no están disponibles en este perfil "
                "(las ventanas privadas no las admiten).",
            )
            return
        manager = extension_manager(self.profile)
        if manager is None:
            manager = self.context.extensions.manager
        ExtensionsDialog(manager, self.context.extensions, self).exec()

    # ------------------------------------------------------- lectura / PiP / privacidad
    def toggle_reader_mode(self) -> None:
        """Muestra u oculta una versión de solo lectura de la página actual."""
        view = self.current_view()
        if view is None:
            self.statusBar().showMessage("Abre una página para usar el modo lectura", 3000)
            return
        theme = "dark" if self.settings.get("theme", "modern") in ("modern", "dark") else "light"
        script = reader_script(
            font_size=int(self.settings.get("reader_font_size", 19)),
            width=int(self.settings.get("reader_width", 720)),
            theme=theme,
        )

        def done(result) -> None:
            if result == "no-article":
                self.statusBar().showMessage(
                    "No se ha podido identificar un artículo en esta página", 5000
                )
            elif result == "ok":
                self.statusBar().showMessage("Modo lectura activado. Pulsa Esc para salir.", 4000)
            elif result == "closed":
                self.statusBar().showMessage("Modo lectura desactivado", 2500)

        try:
            view.page().runJavaScript(script, done)
        except Exception:
            self.statusBar().showMessage("No se pudo activar el modo lectura", 4000)

    def toggle_picture_in_picture(self) -> None:
        """Solicita el PiP nativo de Chromium para el primer vídeo de la página.

        Qt WebEngine no expone una API de PiP: solo se puede pedir desde la
        propia página con `requestPictureInPicture()`. Chromium controla la
        ventana flotante, por lo que Pedrozilla no puede moverla ni
        redimensionarla desde Qt. Si la página no tiene vídeo o el navegador
        rechaza la solicitud, se informa en la barra de estado.
        """
        view = self.current_view()
        if view is None:
            return

        def done(result) -> None:
            messages = {
                "sin-video": "Esta página no contiene vídeo",
                "no-soportado": "Esta página o este motor no permiten Picture in Picture",
                "salir": "Se ha cerrado el vídeo flotante",
                "ok": "Vídeo en ventana flotante (controlada por Chromium)",
            }
            if isinstance(result, str) and result.startswith("error:"):
                messages[result] = "Chromium rechazó Picture in Picture: " + result[7:]
            self.statusBar().showMessage(messages.get(str(result), str(result)), 5000)

        try:
            view.page().runJavaScript(picture_in_picture_script(), done)
        except Exception:
            self.statusBar().showMessage("No se pudo solicitar Picture in Picture", 4000)

    def show_privacy(self) -> None:
        """Abre el centro de privacidad del sitio actual."""
        from .dialogs import PrivacyDialog

        view = self.current_view()
        url = view.url_string() if view is not None else ""
        origin = QUrl(url).host() if url else ""
        cert_info = self._cert_errors.get(origin, "") if hasattr(self, "_cert_errors") else ""
        PrivacyDialog(self.profile, self.settings, url, cert_info, self).exec()

    def apply_settings(self, reload_needed: bool = False) -> None:
        apply_theme(QApplication.instance(), self.settings.get("theme", "classic"))
        self.context.apply_privacy_scripts()
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
            for view in self.views_in_tab(index):
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
            "Se borrarán cookies, caché, historial y el almacenamiento local "
            "de las páginas abiertas de este perfil.\n¿Continuar?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.history.clear()

        # Qt WebEngine no expone una API para vaciar localStorage de todos los
        # orígenes. Sí podemos limpiar el de las páginas abiertas desde la propia
        # página; el resto se elimina del directorio «Local Storage» del perfil.
        for index in range(self.tabs.count()):
            for view in self.views_in_tab(index):
                try:
                    view.page().runJavaScript("try{localStorage.clear()}catch(e){}")
                except RuntimeError:
                    pass
        if not self.incognito:
            storage = Path(self.profile.persistentStoragePath()) / "Local Storage"
            shutil.rmtree(storage, ignore_errors=True)

        self.statusBar().showMessage(
            "Datos de navegación borrados. Recarga las páginas abiertas para ver el cambio.",
            6000,
        )

    # ------------------------------------------------- menús contextuales
    def _reused_action(self, section: str, text: str) -> QAction:
        """Devuelve la QAction original: conserva señales, atajos y estados."""
        action = self._legacy_actions.get((section, self._action_key(text)))
        if action is None:  # Fallback visible si una acción cambió de nombre.
            action = QAction(text, self)
            action.setEnabled(False)
        return action

    def _add_reused(self, menu, section: str, text: str, glyph: str | None = None) -> QAction:
        action = self._reused_action(section, text)
        action.setIcon(menu_icon(text))
        return menu.addAction(action)

    @staticmethod
    def _fade_in_menu(menu: QMenu) -> None:
        """Apertura sutil: fundido de opacidad sin dependencias externas."""
        menu.setWindowOpacity(1.0)
        # Algunas plataformas (p. ej. la plataforma offscreen de pruebas) no
        # soportan opacidad de ventana: animarlas provoca bucles de actualización.
        menu.setWindowOpacity(0.5)
        supported = abs(menu.windowOpacity() - 0.5) < 1e-6
        menu.setWindowOpacity(1.0)
        if not supported:
            return
        try:
            animation = QPropertyAnimation(menu, b"windowOpacity", menu)
            animation.setDuration(130)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            menu.setWindowOpacity(0.0)
            animation.start()
        except (RuntimeError, TypeError, AttributeError):
            menu.setWindowOpacity(1.0)

    def _exec_main_menu(self, menu: QMenu) -> None:
        self._fade_in_menu(menu)
        menu.exec(self._menu_button.mapToGlobal(self._menu_button.rect().bottomLeft()))

    def _show_main_menu(self) -> None:
        """Muestra el menú del botón naranja."""
        self._exec_main_menu(self._build_main_menu())

    def _build_main_menu(self) -> QMenu:
        """Construye el menú reutilizando las QAction de la barra oculta."""
        menu = QMenu(self)
        menu.setObjectName("PedrozillaMainMenu")
        icon = menu_icon

        def add(section: str, text: str, glyph: str) -> QAction:
            return self._add_reused(menu, section, text, glyph)

        menu.addSection("ARCHIVO")
        add("Archivo", "Nueva pestaña", "SP_FileIcon")
        add("Archivo", "Nueva ventana", "SP_FileDialogNewFolder")
        add("Archivo", "Nueva ventana privada", "SP_ComputerIcon")
        menu.addSeparator()
        add("Archivo", "Abrir archivo local", "SP_DialogOpenButton")
        add("Archivo", "Guardar página como", "SP_DialogSaveButton")
        add("Archivo", "Guardar como PDF", "SP_DialogSaveButton")
        add("Archivo", "Imprimir", "SP_DialogPrintButton")
        menu.addSeparator()
        add("Archivo", "Cerrar pestaña", "SP_DialogCloseButton")
        add("Archivo", "Salir", "SP_DialogCloseButton")

        menu.addSection("EDITAR")
        add("Editar", "Deshacer", "SP_ArrowBack")
        add("Editar", "Rehacer", "SP_ArrowForward")
        menu.addSeparator()
        add("Editar", "Cortar", "SP_DialogDiscardButton")
        add("Editar", "Copiar", "SP_FileIcon")
        add("Editar", "Pegar", "SP_DialogApplyButton")
        add("Editar", "Seleccionar todo", "SP_FileDialogContentsView")
        menu.addSeparator()
        add("Editar", "Buscar en la página", "SP_FileDialogInfoView")

        menu.addSection("VER")
        add("Ver", "Recargar", "SP_BrowserReload")
        add("Ver", "Recargar sin caché", "SP_BrowserReload")
        add("Ver", "Detener", "SP_BrowserStop")
        zoom = menu.addMenu(icon("Zoom"), "Zoom")
        self._add_reused(zoom, "Ver", "Aumentar zoom", "SP_ArrowUp")
        self._add_reused(zoom, "Ver", "Reducir zoom", "SP_ArrowDown")
        self._add_reused(zoom, "Ver", "Zoom original", "SP_DialogResetButton")
        add("Ver", "Pantalla completa", "SP_TitleBarMaxButton")
        add("Ver", "Barra de marcadores", "SP_DialogResetButton")
        add("Ver", "Ver código fuente", "SP_FileDialogContentsView")
        add("Ver", "DevTools", "SP_FileDialogDetailedView")
        more = menu.addMenu(icon("Más"), "Más")
        self._add_reused(more, "Ver", "Modo lectura", "SP_FileIcon")
        self._add_reused(more, "Ver", "Vista dividida", "SP_FileDialogDetailedView")
        self._add_reused(more, "Ver", "Vídeo en ventana flotante (PiP)", "SP_MessageBoxInformation")

        menu.addSection("HISTORIAL")
        add("Historial", "Ver historial", "SP_ArrowBack")
        add("Historial", "Reabrir pestaña cerrada", "SP_FileDialogNewFolder")
        navigation = menu.addMenu(icon("Navegación"), "Navegación")
        self._add_reused(navigation, "Historial", "Atrás", "SP_ArrowBack")
        self._add_reused(navigation, "Historial", "Adelante", "SP_ArrowForward")
        self._add_reused(navigation, "Historial", "Página de inicio", "SP_DirHomeIcon")
        self.closed_menu.menuAction().setIcon(icon("Pestañas cerradas recientemente"))
        menu.addMenu(self.closed_menu)
        add("Historial", "Borrar datos de navegación", "SP_DialogDiscardButton")

        menu.addSection("MARCADORES")
        add("Marcadores", "Añadir marcador", "SP_FileIcon")
        add("Marcadores", "Administrar marcadores", "SP_DirIcon")
        add("Marcadores", "Barra de marcadores", "SP_DialogResetButton")

        menu.addSection("DESCARGAS")
        add("Descargas", "Abrir gestor de descargas", "SP_DialogSaveButton")
        add("Descargas", "Abrir carpeta de descargas", "SP_DirOpenIcon")

        menu.addSection("HERRAMIENTAS")
        workspaces = self._workspace_menu()
        workspaces.menuAction().setIcon(icon("Espacios de trabajo"))
        menu.addMenu(workspaces)
        add("Atajos", "Gestionar grupos", "SP_FileDialogDetailedView")
        add("Ajustes", "Extensiones", "SP_FileDialogContentsView")
        add("Ajustes", "Ajustes", "SP_ComputerIcon")
        add("Ajustes", "Privacidad y seguridad", "SP_MessageBoxInformation")

        menu.addSection("AYUDA")
        add("Ayuda", "Buscar actualizaciones", "SP_MessageBoxInformation")
        add("Ayuda", f"Acerca de {BRAND}", "SP_MessageBoxQuestion")

        return menu

    def _show_tab_menu(self, pos) -> None:
        bar = self.tabs.tabBar()
        index = bar.tabAt(pos)
        menu = QMenu(self)
        if index < 0:
            menu.addAction("Nueva pestaña", self.new_tab_focused)
            menu.addAction("Reabrir pestaña cerrada", self.reopen_closed_tab)
            menu.addSeparator()
            menu.addAction("Gestionar grupos de pestañas…", self._manage_groups)
        else:
            menu.addMenu(self._group_submenu(menu, index))
            menu.addSeparator()
            menu.addAction("Recargar", lambda: self._reload_tab(index))
            menu.addAction("Duplicar", lambda: self.new_tab(self._tab_url(index)))
            is_split = isinstance(self.tabs.widget(index), SplitView)
            menu.addAction(
                "Unir vista dividida" if is_split else "Dividir vista",
                self.toggle_split_view,
            )
            if is_split:
                menu.addAction("Intercambiar vistas", self._swap_split_views)
                menu.addAction("Cerrar vista con foco", self._close_split_side)
            menu.addSeparator()
            menu.addAction(
                "Desfijar pestaña" if getattr(self.tabs.widget(index), "_pinned", False)
                else "Fijar pestaña",
                lambda: self.toggle_pin_tab(index),
            )
            views = self.views_in_tab(index)
            page = views[0].page() if views else None
            mute_action = menu.addAction(
                "Activar sonido" if page is not None and page.isAudioMuted() else "Silenciar pestaña",
                lambda: self.toggle_mute_tab(index),
            )
            mute_action.setEnabled(page is not None)
            menu.addSeparator()
            menu.addAction("Cerrar", lambda: self.close_tab(index))
            menu.addAction("Cerrar las demás", lambda: self._close_other_tabs(index))
            menu.addAction("Cerrar las de la derecha", lambda: self._close_tabs_to_right(index))
        menu.exec(bar.mapToGlobal(pos))

    def _reload_tab(self, index: int) -> None:
        for view in self.views_in_tab(index):
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
        # QtPrintSupport solo se carga al imprimir (ahorra trabajo al arrancar).
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter

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
        self._cert_errors[QUrl(url).host()] = f"{url}\n{description}".strip()
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
        # La QMenuBar permanece oculta también en pantalla completa.
        self.menuBar().setVisible(False)
        self.statusBar().setVisible(visible)
        self.bookmarks_bar.setVisible(
            visible and bool(self.settings.get("show_bookmarks_bar"))
        )
        if visible:
            self._rebuild_bookmarks_bar()

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

    # ---------------------------------------------------- actualizaciones
    def schedule_auto_update_check(self) -> None:
        """Comprueba actualizaciones una vez por arranque, sin bloquear."""
        if not self.incognito:
            QTimer.singleShot(3500, self._auto_check_updates)

    def _auto_check_updates(self) -> None:
        if self.incognito or not self.isVisible():
            return
        if not bool(self.settings.get("check_updates", True)):
            return
        now = time.time()
        try:
            last = float(self.settings.get("last_update_check", 0) or 0)
        except (TypeError, ValueError):
            last = 0.0
        if now - last < 24 * 3600:
            return
        # Se marca el intento aunque falle la red: así no se repite la consulta
        # en cada ventana o arranque del mismo día.
        self.settings.set("last_update_check", now)
        self._run_update_check(silent=True)

    def check_updates(self) -> None:
        self._run_update_check(silent=False)

    def _run_update_check(self, *, silent: bool) -> None:
        if self._update_checker is not None:
            if not silent:
                self.statusBar().showMessage("Ya se está comprobando…", 2500)
            return

        # QtNetwork solo se carga cuando hace falta comprobar.
        from .updates import UpdateChecker

        self._update_check_silent = silent
        checker = UpdateChecker(__version__, self)
        self._update_checker = checker
        checker.update_available.connect(self._on_update_available)
        checker.no_update.connect(self._on_update_not_available)
        checker.failed.connect(self._on_update_failed)
        if not silent:
            self.statusBar().showMessage("Buscando actualizaciones…", 3000)
        checker.check()

    def _finish_update_check(self) -> None:
        checker = self._update_checker
        self._update_checker = None
        if checker is not None:
            checker.deleteLater()

    def _on_update_available(self, version: str, url: str, notes: str) -> None:
        silent = self._update_check_silent
        self._finish_update_check()

        if silent:
            if self.settings.get("last_update_prompt") == version:
                self.statusBar().showMessage(
                    f"Actualización disponible: Pedrozilla {version}", 12000
                )
                return
            # Avisa una sola vez por versión; el menú Ayuda siempre permite
            # volver a comprobarlo manualmente.
            self.settings.set("last_update_prompt", version)

        box = QMessageBox(self)
        box.setWindowTitle("Actualización disponible")
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(f"Hay una nueva versión de Pedrozilla: {version}")
        box.setInformativeText(
            f"Tienes la versión {__version__}. ¿Quieres abrir la página de descarga?"
        )
        if notes:
            box.setDetailedText(notes)
        open_button = box.addButton("Abrir descarga", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Más tarde", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_button:
            self.open_url(url, new_tab=True)

    def _on_update_not_available(self) -> None:
        silent = self._update_check_silent
        self._finish_update_check()
        if silent:
            self.statusBar().showMessage("Pedrozilla está actualizado", 4000)
        else:
            QMessageBox.information(
                self,
                "Actualizaciones",
                f"Pedrozilla {__version__} es la última versión disponible.",
            )

    def _on_update_failed(self, message: str) -> None:
        silent = self._update_check_silent
        self._finish_update_check()
        if silent:
            self.statusBar().showMessage("No se pudo comprobar si hay actualizaciones", 5000)
        else:
            QMessageBox.warning(
                self,
                "Actualizaciones",
                f"No se pudo comprobar si hay actualizaciones.\n\n{message}",
            )

    def show_about(self) -> None:
        from .dialogs import AboutDialog

        info = {
            "Versión": __version__,
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
        tabs = []
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            views = self.views_in_tab(index)
            entry = {"url": self._tab_url(index)}
            entry["group"] = getattr(widget, "_group_id", None)
            entry["pinned"] = bool(getattr(widget, "_pinned", False))
            entry["split"] = isinstance(widget, SplitView)
            if isinstance(widget, SplitView):
                entry["split_urls"] = [
                    view.url_string() for view in views if not view.is_new_tab_page
                ]
            if views:
                try:
                    entry["muted"] = bool(
                        views[0].page() is not None and views[0].page().isAudioMuted()
                    )
                except RuntimeError:
                    entry["muted"] = False
            tabs.append(entry)
        self.context.session.save(
            tabs=tabs,
            active=self.tabs.currentIndex(),
            geometry=bytes(self.saveGeometry()),
            maximized=self.isMaximized(),
            groups=self.tab_groups,
        )

    def closeEvent(self, event) -> None:  # noqa: N802 (API de Qt)
        # El historial se escribe con retardo; al cerrar no debe perderse.
        self.context.history.flush()
        # La sesión describe una sola ventana. Solo la escribe la última
        # ventana normal abierta: si varias guardaran, la que se cerrara antes
        # sobrescribiría el estado de las demás.
        last_normal = not self.incognito and sum(
            1 for window in self.context.windows if not window.incognito
        ) == 1
        if last_normal:
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
                # El popup del autocompletado roba y devuelve el foco mientras
                # el usuario escribe (PopupFocusReason). En ese caso NO hay que
                # seleccionar todo: se borraría lo tecleado y cada pulsación
                # empezaría de cero. Solo seleccionamos al entrar de fuera
                # (clic, Ctrl+T, nueva pestaña, cambio de ventana...).
                if event.reason() != Qt.FocusReason.PopupFocusReason:
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

    app.setStyleSheet(stylesheet(theme, close_icon_path()))
    app.setProperty("pedrozilla_theme", theme)
