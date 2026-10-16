"""Hojas de estilo de la interfaz (tema clasico, oscuro y claro).

El tema `classic` imita el Firefox 7 de Windows: franja de pestanas arriba,
barras con degradado gris claro, boton naranja del menu y caja de direcciones
clasica. No hay caja de busqueda aparte: se busca desde la propia omnibox.
"""

from __future__ import annotations

DARK = """
QWidget { background: #202124; color: #e8eaed; font-size: 13px; }
QMainWindow, QDialog { background: #202124; }
QToolBar { background: #292a2d; border: 0; spacing: 4px; padding: 4px 6px; }
QToolBar#BookmarksBar { background: #292a2d; border-top: 1px solid #3c4043; padding: 2px 6px; }
QToolBar::separator { background: #3c4043; width: 1px; margin: 4px 6px; }

QToolButton { background: transparent; border: 0; border-radius: 14px; padding: 5px 9px; color: #e8eaed; }
QToolButton:hover { background: #3c4043; }
QToolButton:pressed { background: #4a4d51; }
QToolButton:checked { background: #8ab4f8; color: #202124; }
QToolButton:disabled { color: #6b6f74; }
QToolButton#BookmarkButton { border-radius: 4px; padding: 3px 8px; max-width: 190px; }
QToolButton#BookmarkButton:hover { background: #3c4043; }

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background: #303134; border: 1px solid #3c4043; border-radius: 15px;
    padding: 6px 12px; selection-background-color: #8ab4f8; selection-color: #202124;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #8ab4f8; background: #303134;
}
QLineEdit#Omnibox { font-size: 14px; padding: 7px 14px; }
QLineEdit#FindInput { border-radius: 4px; padding: 4px 8px; }

QComboBox::drop-down { border: 0; width: 18px; }
QComboBox QAbstractItemView { background: #303134; border: 1px solid #3c4043; }

QPushButton {
    background: #303134; border: 1px solid #3c4043; border-radius: 5px;
    padding: 6px 14px; min-width: 72px;
}
QPushButton:hover { background: #3c4043; }
QPushButton:pressed { background: #4a4d51; }
QPushButton:default { background: #8ab4f8; color: #202124; border: 0; }
QPushButton:default:hover { background: #aecbfa; }

QTabWidget::pane { border: 0; }
QTabBar { background: #292a2d; qproperty-drawBase: 0; }
QTabBar::tab {
    background: #292a2d; color: #bdc1c6; border: 0; border-right: 1px solid #202124;
    padding: 7px 10px; min-width: 110px; max-width: 240px;
}
QTabBar::tab:hover { background: #3c4043; }
QTabBar::tab:selected { background: #202124; color: #ffffff; }
QTabBar::close-button { __CLOSE_BUTTON__ }
QTabBar QToolButton { border: 0; }

QMenuBar { background: #292a2d; }
QMenuBar::item { padding: 6px 10px; background: transparent; }
QMenuBar::item:selected { background: #3c4043; }
QMenu { background: #292a2d; border: 1px solid #3c4043; padding: 4px; }
QMenu::item { padding: 6px 26px 6px 22px; border-radius: 4px; }
QMenu::item:selected { background: #3c4043; }
QMenu::item:disabled { color: #6b6f74; }
QMenu::separator { height: 1px; background: #3c4043; margin: 4px 8px; }

QHeaderView::section {
    background: #292a2d; border: 0; border-right: 1px solid #3c4043;
    border-bottom: 1px solid #3c4043; padding: 6px 8px; font-weight: 600;
}
QTableView, QTreeView, QListView { background: #202124; alternate-background-color: #242528;
    border: 0; gridline-color: #3c4043; selection-background-color: #3c4043; }
QTableView::item:selected, QTreeView::item:selected, QListView::item:selected { background: #3c4043; }

QTabWidget#DialogTabs QTabBar::tab { min-width: 90px; border-radius: 4px; margin-right: 2px; }

QProgressBar { background: #303134; border: 0; border-radius: 4px; text-align: center; height: 8px; color: #e8eaed; }
QProgressBar::chunk { background: #8ab4f8; border-radius: 4px; }

QStatusBar { background: #292a2d; color: #9aa0a6; }
QStatusBar::item { border: 0; }
QScrollBar:vertical { background: transparent; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #5f6368; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:hover { background: #80868b; }
QScrollBar:horizontal { background: transparent; height: 12px; }
QScrollBar::handle:horizontal { background: #5f6368; border-radius: 6px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QLabel#PanelTitle { font-size: 15px; font-weight: 600; }
QLabel#MutedHint { color: #9aa0a6; }
QFrame#DownloadsBar { background: #292a2d; border-top: 1px solid #3c4043; }
QFrame#FindBar { background: #292a2d; border-top: 1px solid #3c4043; }
QWidget#NewTabBadge { background: #303134; border-radius: 12px; }
QToolButton#MenuButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffb054, stop:0.5 #f7941e, stop:1 #e87b0b);
    border: 1px solid #c96a09; border-radius: 3px; color: #ffffff; font-weight: 700; padding: 5px 14px;
}
QToolButton#MenuButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffcd85, stop:0.5 #ffa631, stop:1 #ee8a12); }
QToolButton#MenuButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e08b1c, stop:1 #c96f08); }
"""

LIGHT = """
QWidget { background: #ffffff; color: #202124; font-size: 13px; }
QMainWindow, QDialog { background: #ffffff; }
QToolBar { background: #f1f3f4; border: 0; spacing: 4px; padding: 4px 6px; }
QToolBar#BookmarksBar { background: #f8f9fa; border-top: 1px solid #dadce0; padding: 2px 6px; }
QToolBar::separator { background: #dadce0; width: 1px; margin: 4px 6px; }

QToolButton { background: transparent; border: 0; border-radius: 14px; padding: 5px 9px; }
QToolButton:hover { background: #e8eaed; }
QToolButton:pressed { background: #dadce0; }
QToolButton:checked { background: #1a73e8; color: #ffffff; }
QToolButton:disabled { color: #bdc1c6; }
QToolButton#BookmarkButton { border-radius: 4px; padding: 3px 8px; max-width: 190px; }
QToolButton#BookmarkButton:hover { background: #e8eaed; }
QToolButton#MenuButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffb054, stop:0.5 #f7941e, stop:1 #e87b0b);
    border: 1px solid #c96a09; border-radius: 3px; color: #ffffff; font-weight: 700; padding: 5px 14px;
}
QToolButton#MenuButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffcd85, stop:0.5 #ffa631, stop:1 #ee8a12); }
QToolButton#MenuButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e08b1c, stop:1 #c96f08); }

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background: #f1f3f4; border: 1px solid #f1f3f4; border-radius: 15px; padding: 6px 12px;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #1a73e8; background: #ffffff;
}
QLineEdit#Omnibox { font-size: 14px; padding: 7px 14px; }
QLineEdit#FindInput { border-radius: 4px; padding: 4px 8px; }
QComboBox::drop-down { border: 0; width: 18px; }
QComboBox QAbstractItemView { background: #ffffff; border: 1px solid #dadce0; }

QPushButton { background: #f1f3f4; border: 1px solid #dadce0; border-radius: 5px; padding: 6px 14px; min-width: 72px; }
QPushButton:hover { background: #e8eaed; }
QPushButton:default { background: #1a73e8; color: #ffffff; border: 0; }
QPushButton:default:hover { background: #1b66c9; }

QTabWidget::pane { border: 0; }
QTabBar { background: #f1f3f4; qproperty-drawBase: 0; }
QTabBar::tab { background: #f1f3f4; color: #3c4043; border: 0; border-right: 1px solid #dadce0;
    padding: 7px 10px; min-width: 110px; max-width: 240px; }
QTabBar::tab:hover { background: #e8eaed; }
QTabBar::tab:selected { background: #ffffff; color: #202124; }
QTabBar::close-button { __CLOSE_BUTTON__ }

QMenuBar { background: #f1f3f4; }
QMenuBar::item { padding: 6px 10px; background: transparent; }
QMenuBar::item:selected { background: #e8eaed; }
QMenu { background: #ffffff; border: 1px solid #dadce0; padding: 4px; }
QMenu::item { padding: 6px 26px 6px 22px; border-radius: 4px; }
QMenu::item:selected { background: #e8eaed; }
QMenu::separator { height: 1px; background: #dadce0; margin: 4px 8px; }

QHeaderView::section { background: #f8f9fa; border: 0; border-right: 1px solid #dadce0;
    border-bottom: 1px solid #dadce0; padding: 6px 8px; font-weight: 600; }
QTableView, QTreeView, QListView { background: #ffffff; alternate-background-color: #f8f9fa;
    border: 0; gridline-color: #dadce0; selection-background-color: #e8f0fe; }
QTableView::item:selected, QTreeView::item:selected, QListView::item:selected { background: #e8f0fe; }

QProgressBar { background: #e8eaed; border: 0; border-radius: 4px; text-align: center; height: 8px; }
QProgressBar::chunk { background: #1a73e8; border-radius: 4px; }

QStatusBar { background: #f8f9fa; color: #5f6368; }
QStatusBar::item { border: 0; }
QScrollBar:vertical { background: transparent; width: 12px; }
QScrollBar::handle:vertical { background: #bdc1c6; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #9aa0a6; }
QScrollBar:horizontal { background: transparent; height: 12px; }
QScrollBar::handle:horizontal { background: #bdc1c6; border-radius: 6px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QLabel#PanelTitle { font-size: 15px; font-weight: 600; }
QLabel#MutedHint { color: #5f6368; }
QFrame#DownloadsBar { background: #f8f9fa; border-top: 1px solid #dadce0; }
QFrame#FindBar { background: #f8f9fa; border-top: 1px solid #dadce0; }
QWidget#NewTabBadge { background: #f1f3f4; border-radius: 12px; }
"""


CLASSIC = """
QWidget { background: #f0f0f0; color: #1a1a1a; font-size: 13px; }
QMainWindow, QDialog { background: #f0f0f0; }
QToolTip { background: #ffffe1; color: #000000; border: 1px solid #8a8a5c; padding: 2px 4px; }

QWidget#TabStrip {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #eef1f5, stop:0.55 #dde2e9, stop:1 #cfd6df);
    border-bottom: 1px solid #a6adb8;
}

QTabWidget::pane { border: 0; }
QTabBar { background: transparent; qproperty-drawBase: 0; }
QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dfe4ea, stop:1 #c9d0da);
    color: #333333; border: 1px solid #a6adb8; border-bottom: 0;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
    padding: 5px 10px; margin-right: 2px; margin-top: 3px;
    min-width: 100px; max-width: 220px;
}
QTabBar::tab:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f3f5f8, stop:1 #e3e8ee);
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f5f6f8);
    color: #111111; margin-top: 0; padding: 6px 12px 6px 12px; border-color: #8f97a3;
}
QTabBar::close-button { __CLOSE_BUTTON__ }
QTabBar QToolButton { border: 0; background: transparent; }

QToolBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fbfbfb, stop:0.5 #f2f2f2, stop:1 #e6e6e6);
    border: 0; border-bottom: 1px solid #b6b6b6; spacing: 3px; padding: 4px 6px; }
QToolBar#BookmarksBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f4f5f7, stop:1 #e8eaee);
    border-bottom: 1px solid #c4c8ce; padding: 2px 6px; }
QToolBar::separator { background: #c4c8ce; width: 1px; margin: 4px 6px; }

QToolButton { background: transparent; border: 1px solid transparent; border-radius: 3px; padding: 4px 7px; color: #333333; }
QToolButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #e4e6ea);
    border: 1px solid #a8afb8; }
QToolButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d6dae0, stop:1 #c6cbd3);
    border-color: #8f97a3; }
QToolButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cfe0f5, stop:1 #b9d2ee);
    border: 1px solid #7fa6d0; color: #10314f; }
QToolButton:disabled { color: #a0a0a0; }
QToolButton#BookmarkButton { border-radius: 3px; padding: 3px 8px; max-width: 190px; }
QToolButton#BookmarkButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #e4e6ea);
    border: 1px solid #a8afb8; }
QToolButton#MenuButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffc06a, stop:0.5 #f7941e, stop:1 #e07b09);
    border: 1px solid #b96a08; border-radius: 3px; color: #ffffff; font-weight: 700; padding: 5px 14px;
}
QToolButton#MenuButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffcd85, stop:0.5 #ffa631, stop:1 #ee8a12); }
QToolButton#MenuButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e08b1c, stop:1 #c96f08); }

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {
    background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 4px 8px;
    selection-background-color: #3399ff; selection-color: #ffffff; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #4a90e2; }
QLineEdit#Omnibox { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 4px 8px; font-size: 13px; }
QLineEdit#Omnibox:focus { border: 1px solid #4a90e2; }
QLineEdit#FindInput { padding: 4px 8px; }
QComboBox::drop-down { border: 0; width: 18px; background: transparent; }
QComboBox QAbstractItemView { background: #ffffff; border: 1px solid #a0a0a0; selection-background-color: #d7e7f8; selection-color: #111111; }

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fdfeff, stop:0.5 #f1f2f4, stop:1 #e3e5e8);
    border: 1px solid #a8adb4; border-radius: 3px; padding: 5px 14px; min-width: 72px; color: #1a1a1a; }
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:0.5 #f7faff, stop:1 #eaf2fd);
    border-color: #7fa6d0; }
QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d5dbe3, stop:1 #c9d0d9); }
QPushButton:default {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffc06a, stop:0.5 #f7941e, stop:1 #e07b09);
    border: 1px solid #b96a08; color: #ffffff; font-weight: 600; }
QPushButton:disabled { color: #9a9a9a; background: #ececed; border-color: #c6c9cd; }

QMenuBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7f8fa, stop:1 #e9ebee); border-bottom: 1px solid #c0c4ca; }
QMenuBar::item { padding: 5px 9px; background: transparent; }
QMenuBar::item:selected { background: #dbe7f6; border: 1px solid #a8c9e8; border-radius: 3px; padding: 4px 8px; }
QMenu { background: #ffffff; border: 1px solid #9a9a9a; padding: 3px; }
QMenu::item { padding: 5px 26px 5px 22px; border-radius: 3px; }
QMenu::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e8f1fb, stop:1 #d3e4f7); color: #111111; }
QMenu::item:disabled { color: #a0a0a0; }
QMenu::separator { height: 1px; background: #dcdfe4; margin: 4px 8px; }

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7f8f9, stop:1 #e9ebed);
    border: 0; border-right: 1px solid #cbd0d6; border-bottom: 1px solid #b9bfc6; padding: 5px 8px; font-weight: 600; }
QTableView, QTreeView, QListView {
    background: #ffffff; alternate-background-color: #f6f7f9; border: 1px solid #c3c8ce; gridline-color: #dcdfe3;
    selection-background-color: #d7e7f8; selection-color: #111111; }
QTableView::item:selected, QTreeView::item:selected, QListView::item:selected { background: #d7e7f8; color: #111111; }

QProgressBar { background: #ffffff; border: 1px solid #b2b7bd; border-radius: 3px; text-align: center; height: 10px; color: #333333; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffc978, stop:1 #f7941e); border-radius: 2px; }

QStatusBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f3f4f6, stop:1 #e6e8eb); color: #4a4a4a; border-top: 1px solid #c3c8ce; }
QStatusBar::item { border: 0; }

QScrollBar:vertical { background: #f0f1f3; width: 15px; border-left: 1px solid #d3d6da; }
QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #cdd2d8, stop:0.5 #e9ebee, stop:1 #c7ccd3);
    border: 1px solid #b2b7bd; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #bcc3cc; }
QScrollBar:horizontal { background: #f0f1f3; height: 15px; border-top: 1px solid #d3d6da; }
QScrollBar::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cdd2d8, stop:0.5 #e9ebee, stop:1 #c7ccd3);
    border: 1px solid #b2b7bd; border-radius: 3px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QLabel#PanelTitle { font-size: 15px; font-weight: 600; }
QLabel#MutedHint { color: #6b6b6b; }
QFrame#DownloadsBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7f8fa, stop:1 #eaecf0); border-top: 1px solid #c3c8ce; }
QFrame#FindBar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7f8fa, stop:1 #e9ebee); border-top: 1px solid #c3c8ce; }
QWidget#NewTabBadge { background: #ffffff; border: 1px solid #c9ced5; border-radius: 10px; }
QTabWidget#DialogTabs QTabBar::tab { min-width: 90px; border-radius: 4px; margin-right: 2px; }
"""


def stylesheet(theme: str, close_icon: str = "") -> str:
    """Devuelve la hoja de estilo del tema indicado.

    `close_icon` es la ruta del icono «X» de las pestañas que se inyecta en
    `QTabBar::close-button`; si no se indica, las pestañas no muestran botón.
    """
    theme = (theme or "").lower()
    if theme == "light":
        css = LIGHT
    elif theme == "classic":
        css = CLASSIC
    else:
        css = DARK

    if close_icon:
        # Qt espera separadores "/" también en Windows.
        css = css.replace("__CLOSE_BUTTON__", f"image: url({close_icon.replace(chr(92), '/')});")
    else:
        css = css.replace("__CLOSE_BUTTON__", "image: none;")
    return css
