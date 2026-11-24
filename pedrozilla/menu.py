"""Menú principal compacto y desplazable de Pedrozilla.

El menú nativo de Qt crece sin límite con las acciones, así que aquí se
presentan las entradas en un `QTreeWidget` dentro de un `QMenu`. La lista tiene
una altura máxima y scroll: todas las opciones siguen accesibles sin que el
desplegable ocupe media pantalla.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPoint, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QWidgetAction,
)

#: Papel donde se guarda el tipo y la acción/submenú de cada fila.
ENTRY_ROLE = Qt.ItemDataRole.UserRole
ACTION_ROLE = Qt.ItemDataRole.UserRole + 1
SUBMENU_ROLE = Qt.ItemDataRole.UserRole + 2


@dataclass
class MenuEntry:
    """Una fila del menú principal."""

    kind: str  # section | action | separator | submenu
    text: str = ""
    action: QAction | None = None
    submenu: QMenu | None = None


class ScrollableMenu(QMenu):
    """QMenu con las entradas en una lista desplazable."""

    def __init__(self, entries: list[MenuEntry], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PedrozillaMainMenu")
        self.entries = list(entries)
        self._tree = self._build_tree()
        self._tree.installEventFilter(self)
        self._tree.viewport().installEventFilter(self)
        self._tree.itemClicked.connect(self._activate)
        self.aboutToShow.connect(self._focus_tree)

        holder = QWidget(self)
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self._tree)

        container = QWidgetAction(self)
        container.setDefaultWidget(holder)
        self.addAction(container)

    @property
    def tree(self) -> QTreeWidget:
        """Lista interna (útil para pruebas y depuración)."""
        return self._tree

    # -- construcción -------------------------------------------------------
    def _build_tree(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setObjectName("PedrozillaMenuList")
        tree.setColumnCount(2)
        tree.setHeaderHidden(True)
        tree.setIndentation(0)
        tree.setRootIsDecorated(False)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tree.setMouseTracking(True)
        tree.setColumnWidth(0, 270)
        tree.setColumnWidth(1, 90)
        tree.setMinimumWidth(372)

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry().height() if screen else 900
        tree.setMaximumHeight(max(300, min(560, int(available * 0.62))))
        self._apply_palette(tree)

        for entry in self.entries:
            if entry.kind == "separator":
                self._add_separator(tree)
                continue
            self._add_row(tree, entry)
        return tree

    @staticmethod
    def _apply_palette(tree: QTreeWidget) -> None:
        palette = tree.palette()
        window = palette.color(QPalette.ColorRole.Window).name()
        text = palette.color(QPalette.ColorRole.WindowText).name()
        highlight = palette.color(QPalette.ColorRole.Highlight).name()
        highlighted_text = palette.color(QPalette.ColorRole.HighlightedText).name()
        mid = palette.color(QPalette.ColorRole.Mid).name()
        hover = QColor(highlight).lighter(185).name()
        tree.setStyleSheet(
            f"""
            QTreeWidget#PedrozillaMenuList {{
                background: {window}; color: {text}; border: 0; outline: 0;
                font-size: 14px;
            }}
            QTreeWidget#PedrozillaMenuList::item {{
                padding: 4px 6px; border-radius: 6px;
            }}
            QTreeWidget#PedrozillaMenuList::item:hover {{ background: {hover}; }}
            QTreeWidget#PedrozillaMenuList::item:selected {{
                background: {highlight}; color: {highlighted_text};
            }}
            QTreeWidget#PedrozillaMenuList::item:disabled {{ color: {mid}; }}
            QFrame#MenuSeparatorLine {{ color: {mid}; background: {mid}; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
            QScrollBar::handle:vertical {{
                background: {mid}; border-radius: 4px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                height: 0; background: transparent;
            }}
            """
        )

    @staticmethod
    def _add_separator(tree: QTreeWidget) -> None:
        item = QTreeWidgetItem(tree)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setSizeHint(0, QSize(10, 9))
        line = QFrame(tree)
        line.setObjectName("MenuSeparatorLine")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        holder = QWidget(tree)
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.addWidget(line)
        tree.setItemWidget(item, 0, holder)
        item.setData(0, ENTRY_ROLE, "separator")

    @staticmethod
    def _add_row(tree: QTreeWidget, entry: MenuEntry) -> None:
        item = QTreeWidgetItem(tree)
        if entry.kind == "section":
            item.setText(0, entry.text)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setSizeHint(0, QSize(10, 32))
            item.setData(0, ENTRY_ROLE, "section")
            return

        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item.setSizeHint(0, QSize(10, 34))
        if entry.action is not None:
            item.setText(0, entry.text)
            item.setIcon(0, entry.action.icon())
            shortcut = entry.action.shortcut().toString()
            if shortcut:
                item.setText(1, shortcut)
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setData(0, ENTRY_ROLE, "action")
            item.setData(0, ACTION_ROLE, entry.action)
        elif entry.submenu is not None:
            item.setText(0, f"{entry.text}  ▸")
            item.setIcon(0, entry.submenu.menuAction().icon())
            item.setData(0, ENTRY_ROLE, "submenu")
            item.setData(0, SUBMENU_ROLE, entry.submenu)

    # -- interacción --------------------------------------------------------
    def _focus_tree(self) -> None:
        first = None
        for index in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(index)
            if item.data(0, ENTRY_ROLE) == "action":
                first = item
                break
        if first is not None:
            self._tree.setCurrentItem(first)
        QTimer.singleShot(0, self._tree.setFocus)

    def _activate(self, item: QTreeWidgetItem | None, _column: int = 0) -> None:
        if item is None:
            return
        kind = item.data(0, ENTRY_ROLE)
        if kind == "action":
            action = item.data(0, ACTION_ROLE)
            if action is not None and action.isEnabled():
                action.trigger()
                self.close()
        elif kind == "submenu":
            submenu = item.data(0, SUBMENU_ROLE)
            if submenu is not None:
                rect = self._tree.visualItemRect(item)
                point = QPoint(self._tree.viewport().width() - 4, rect.top())
                submenu.exec(self._tree.viewport().mapToGlobal(point))

    def eventFilter(self, obj, event):  # noqa: N802 (API de Qt)
        if obj in (self._tree, self._tree.viewport()) and isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._activate(self._tree.currentItem())
                return True
            if event.key() == Qt.Key.Key_Escape:
                self.close()
                return True
            if event.key() == Qt.Key.Key_Right:
                item = self._tree.currentItem()
                if item is not None and item.data(0, ENTRY_ROLE) == "submenu":
                    self._activate(item)
                    return True
        return super().eventFilter(obj, event)
