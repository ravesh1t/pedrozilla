"""Extensiones Chromium (Manifest V3) para Pedrozilla.

Qt WebEngine 6.10+ expone QWebEngineExtensionManager, compatible con el
formato de extensiones de Chrome/Firefox. Resumen de la API:

- installExtension(ruta): instala una carpeta o .zip con manifest.json en el
  directorio del perfil (installPath) y la carga. Qt la vuelve a cargar solo
  en cada arranque, siempre DESACTIVADA.
- loadExtension(ruta): carga temporal (no persiste).
- setExtensionEnabled(info, bool): activa/desactiva en caliente.
- uninstallExtension / unloadExtension: quitan archivos o liberan memoria.
- Señales installFinished / loadFinished / uninstallFinished / unloadFinished.

Como Qt no recuerda qué extensiones tenía el usuario ACTIVAS, ese estado se
persiste en settings.json (clave "enabled_extensions") y se restaura con
ExtensionBridge cada vez que Qt termina de cargar una extensión.

Solo se admiten manifiestos MV3 y no está disponible en perfiles privados
(off-the-record), que es lo que distingue a una ventana incógnito.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def extension_manager(profile) -> Any | None:
    """Gestor de extensiones del perfil, o None si no está disponible.

    Los perfiles off-the-record (ventanas privadas) no soportan extensiones:
    en ellos Qt no ofrece gestor y devolvemos None para que la UI lo indique.
    """
    getter = getattr(profile, "extensionManager", None)
    if getter is None:
        return None
    try:
        return getter()
    except Exception:  # pragma: no cover - defensa ante perfiles sin API
        return None


# -- acceso a QWebEngineExtensionInfo ----------------------------------------
# En PySide6 estos campos vienen como métodos (info.name()); en otras
# versiones podrían ser atributos. Los helpers admiten ambos formatos.

def _field(info, name: str) -> Any:
    value = getattr(info, name, None)
    return value() if callable(value) else value


def ext_id(info) -> str:
    return str(_field(info, "id") or "")


def ext_name(info) -> str:
    return str(_field(info, "name") or "") or ext_id(info)


def ext_error(info) -> str:
    return str(_field(info, "error") or "")


def ext_path(info) -> str:
    return str(_field(info, "path") or "")


def ext_is_enabled(info) -> bool:
    return bool(_field(info, "isEnabled"))


def ext_is_installed(info) -> bool:
    return bool(_field(info, "isInstalled"))


def ext_is_loaded(info) -> bool:
    return bool(_field(info, "isLoaded"))


class ExtensionBridge(QObject):
    """Persiste el estado «activada» de las extensiones entre sesiones.

    Qt carga las extensiones instaladas desactivadas en cada arranque (y de
    forma asíncrona), así que restauramos la activación tanto al crear el
    puente como en cada señal loadFinished.

    Nota: setExtensionEnabled() lanzado dentro del manejador de una señal del
    propio gestor (installFinished/loadFinished) provoca un access violation
    en Chromium. Por eso toda activación se difiere al siguiente ciclo de
    eventos y se usa una referencia fresca de extensions().
    """

    changed = Signal()  # el estado activo cambió (para refrescar la UI)

    def __init__(self, manager: Any, settings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.settings = settings
        manager.loadFinished.connect(self._on_load_finished)
        manager.installFinished.connect(self._on_install_finished)

    # -- utilidades ----------------------------------------------------------
    def find(self, extension_id: str):
        """Referencia fresca de la extensión, o None si ya no existe."""
        for info in self.manager.extensions():
            if ext_id(info) == extension_id:
                return info
        return None

    # -- estado persistido ---------------------------------------------------
    def enabled_ids(self) -> set[str]:
        return {str(x) for x in (self.settings.get("enabled_extensions") or [])}

    def _store(self, ids: set[str]) -> None:
        self.settings.set("enabled_extensions", sorted(ids))

    def set_enabled(self, info, enabled: bool) -> None:
        """Activa/desactiva una extensión (diferido) y lo guarda en settings."""
        self._schedule(ext_id(info), enabled)

    def _schedule(self, extension_id: str, enabled: bool) -> None:
        QTimer.singleShot(0, lambda: self._set_now(extension_id, enabled))

    def _set_now(self, extension_id: str, enabled: bool) -> None:
        fresh = self.find(extension_id)
        if fresh is None:
            return
        self.manager.setExtensionEnabled(fresh, enabled)
        ids = self.enabled_ids()
        if enabled:
            ids.add(extension_id)
        else:
            ids.discard(extension_id)
        self._store(ids)
        self.changed.emit()

    def forget(self, info) -> None:
        """Olvida el estado guardado (al desinstalar)."""
        ids = self.enabled_ids()
        ids.discard(ext_id(info))
        self._store(ids)

    def restore(self) -> None:
        """Reactiva lo que el usuario había dejado activo."""
        wanted = self.enabled_ids()
        if not wanted:
            return
        for info in self.manager.extensions():
            if ext_id(info) in wanted and not ext_is_enabled(info):
                # Referencia fresca de extensions() y fuera de toda señal:
                # es el único patrón seguro con setExtensionEnabled().
                self._schedule(ext_id(info), True)

    def _on_load_finished(self, info) -> None:
        # Qt termina de cargar (desactivada); si el usuario la tenía activa,
        # la volvemos a activar. Si el fallo es del propio Qt lo ignoramos
        # aquí: el diálogo muestra ext_error(info).
        extension_id = ext_id(info)
        if ext_is_loaded(info) and extension_id in self.enabled_ids() and not ext_is_enabled(info):
            self._schedule(extension_id, True)

    def _on_install_finished(self, info) -> None:
        # Al instalar con éxito se activa automáticamente (como haría Chrome);
        # vive en el puente —y no en el diálogo— para funcionar con cualquier
        # instalación, esté o no abierta la ventana de extensiones. La llamada
        # a setExtensionEnabled se difiere: dentro de la señal, crashea.
        if ext_is_installed(info) and not ext_error(info):
            self._schedule(ext_id(info), True)


class ExtensionsDialog(QDialog):
    """Ventana «Extensiones» para instalar, activar y quitar extensiones."""

    def __init__(self, manager: Any, bridge: ExtensionBridge, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.bridge = bridge
        self._refreshing = False
        self._updating_check = False
        self.setWindowTitle("Extensiones")
        self.setMinimumSize(560, 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Extensiones")
        title.setObjectName("PanelTitle")
        layout.addWidget(title)

        hint = QLabel(
            "Instala extensiones de Chrome con manifiesto v3 (MV3): una carpeta "
            "desempaquetada o un archivo .zip que contenga el manifest.json en la "
            "raíz. Se guardan en el perfil y Qt las recarga en cada arranque."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Lista de extensiones con casilla de activación por elemento.
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setAlternatingRowColors(True)
        self.list.setMinimumHeight(240)
        self.list.currentItemChanged.connect(lambda *_: self._sync_controls())
        self.list.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list, 1)

        # Carpeta de instalación de Qt (referencia útil para el usuario).
        install_path = _field(manager, "installPath") or ""
        path_label = QLabel(f"Carpeta de instalación: {install_path}")
        path_label.setObjectName("MutedLabel")
        path_label.setToolTip(install_path)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(path_label)

        # Fila de acciones.
        row = QHBoxLayout()
        row.setSpacing(8)
        self.btn_install_dir = QPushButton("Instalar carpeta…")
        self.btn_install_dir.clicked.connect(self._install_folder)
        row.addWidget(self.btn_install_dir)
        self.btn_install_zip = QPushButton("Instalar .zip…")
        self.btn_install_zip.clicked.connect(self._install_zip)
        row.addWidget(self.btn_install_zip)
        self.btn_uninstall = QPushButton("Desinstalar")
        self.btn_uninstall.clicked.connect(self._uninstall)
        row.addWidget(self.btn_uninstall)
        row.addStretch(1)
        self.check_enabled = QPushButton("Activar")  # con estado de casilla
        self.check_enabled.setCheckable(True)
        self.check_enabled.setFixedWidth(96)
        self.check_enabled.toggled.connect(self._on_toggle_clicked)
        row.addWidget(self.check_enabled)
        layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        # Refrescar ante cualquier cambio del gestor; el resultado de la
        # instalación tiene su manejo propio (aviso + activación).
        manager.installFinished.connect(self._on_install_finished)
        manager.loadFinished.connect(lambda _info: self.refresh())
        manager.uninstallFinished.connect(lambda _info: self.refresh())
        manager.unloadFinished.connect(lambda _info: self.refresh())
        # El puente difiere las activaciones: refrescamos cuando confirme.
        bridge.changed.connect(self.refresh)

        self.refresh()
        self._sync_controls()

    # -- estado y pintado ----------------------------------------------------
    @staticmethod
    def _state_text(info) -> str:
        error = ext_error(info)
        if error:
            return f"error: {error}"
        if ext_is_enabled(info):
            return "activa"
        if ext_is_installed(info):
            return "instalada (desactivada)"
        if ext_is_loaded(info):
            return "cargada (temporal, desactivada)"
        return "no cargada"

    def refresh(self, focus_id: str | None = None) -> None:
        """Vuelve a dibujar la lista con el estado actual del gestor."""
        self._refreshing = True
        current = focus_id
        if current is None and self.list.currentItem() is not None:
            current = ext_id(self.list.currentItem().data(Qt.ItemDataRole.UserRole))
        self.list.clear()
        for info in self.manager.extensions():
            item = QListWidgetItem(f"{ext_name(info)} — {self._state_text(info)}")
            item.setData(Qt.ItemDataRole.UserRole, info)
            item.setToolTip(
                f"ID: {ext_id(info)}\nRuta: {ext_path(info)}\n{self._state_text(info)}"
            )
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setCheckState(
                Qt.CheckState.Checked if ext_is_enabled(info) else Qt.CheckState.Unchecked
            )
            self.list.addItem(item)
            if current is not None and ext_id(info) == current:
                self.list.setCurrentItem(item)
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)
        self._refreshing = False
        self._sync_controls()

    def _current_info(self):
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def _sync_controls(self) -> None:
        info = self._current_info()
        self.check_enabled.setEnabled(info is not None and ext_is_loaded(info))
        self.btn_uninstall.setEnabled(info is not None and ext_is_installed(info))
        if info is not None:
            self._updating_check = True
            self.check_enabled.setChecked(ext_is_enabled(info))
            self._updating_check = False

    # -- acciones ------------------------------------------------------------
    def _install_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Selecciona la carpeta de la extensión (con manifest.json)"
        )
        if directory:
            self.manager.installExtension(directory)

    def _install_zip(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Selecciona el archivo de la extensión", "", "Extensiones (*.zip)"
        )
        if filename:
            self.manager.installExtension(filename)

    def _on_install_finished(self, info) -> None:
        # El puente activa la extensión si todo fue bien; aquí solo avisamos
        # si Qt rechazó el paquete.
        error = ext_error(info)
        if error or not ext_is_installed(info):
            QMessageBox.warning(
                self,
                "No se pudo instalar la extensión",
                f"Qt rechazó el paquete:\n{error or 'manifest.json no válido'}\n\n"
                "Recuerda: solo manifiestos MV3 con manifest.json en la raíz.",
            )
        self.refresh(ext_id(info))

    def _uninstall(self) -> None:
        info = self._current_info()
        if info is None:
            return
        answer = QMessageBox.question(
            self,
            "Desinstalar extensión",
            f"¿Quitar «{ext_name(info)}» y sus archivos del perfil?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.bridge.forget(info)
            self.manager.uninstallExtension(info)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._refreshing:
            return
        info = item.data(Qt.ItemDataRole.UserRole)
        if info is None:
            return
        # Cambio vía la casilla de la propia fila.
        self._apply_enabled(info, item.checkState() == Qt.CheckState.Checked)

    def _on_toggle_clicked(self, checked: bool) -> None:
        if self._updating_check:
            return
        info = self._current_info()
        if info is None:
            return
        self._apply_enabled(info, checked)

    def _apply_enabled(self, info, enabled: bool) -> None:
        # El cambio real se difiere en el puente (seguridad con Chromium) y
        # su señal changed() refresca la lista cuando ya está aplicado.
        self.bridge.set_enabled(info, enabled)
