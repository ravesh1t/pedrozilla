"""Hojas de estilo de la interfaz (tema oscuro y claro)."""

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
QTabBar::close-button { image: none; }
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
QTabBar::close-button { image: none; }

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


def stylesheet(theme: str) -> str:
    return LIGHT if (theme or "").lower() == "light" else DARK
