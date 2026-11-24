"""Pruebas locales de Pedrozilla (unittest, sin dependencias nuevas).

Se ejecutan con:

    QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v

Las pruebas que abren una ventana usan un directorio de configuración temporal
para no tocar el perfil real del usuario.
"""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from collections import defaultdict


class NewTabTests(unittest.TestCase):
    def test_generated_html_has_no_placeholders(self) -> None:
        from pedrozilla.newtab import new_tab_html

        html = new_tab_html(
            search_template="https://duckduckgo.com/?q={query}",
            engine_key="duckduckgo",
            theme="modern",
            shortcuts=[{"title": "Ejemplo", "url": "https://example.com"}],
            history=[{"title": "Wiki", "url": "https://es.wikipedia.org/", "visits": 4}],
            accent="#e58b36",
            brand="Pedrozilla",
            newtab_prefs={"dashboard": "{}"},
            workspaces={"personal": {"name": "Personal"}},
            active_workspace="personal",
        )
        self.assertFalse(re.findall(r"__[A-Z_]+__", html))
        self.assertIn("location.href = target;", html)
        self.assertIn('class="wallpaper"', html)
        self.assertIn('data-section="notes"', html)
        self.assertIn('id="workOptions"', html)
        self.assertIn("window.pedrozilla.setNewTabPrefs", html)
        self.assertIn('"workspace": "Personal"', html)
        self.assertIn("https://example.com", html)
        self.assertIn("https://duckduckgo.com/?q={query}", html)

    def test_reader_and_pip_scripts(self) -> None:
        from pedrozilla.reader import picture_in_picture_script, reader_script

        script = reader_script(font_size=21, width=800, theme="dark")
        self.assertNotIn("__PZ_", script)
        self.assertIn("no-article", script)
        self.assertIn("Escape", script)
        pip = picture_in_picture_script()
        self.assertIn("requestPictureInPicture", pip)
        self.assertIn("sin-video", pip)

    def test_default_settings_include_new_features(self) -> None:
        from pedrozilla.storage import DEFAULT_SETTINGS

        self.assertEqual(DEFAULT_SETTINGS["theme"], "modern")
        for key in (
            "newtab_prefs",
            "reader_font_size",
            "reader_width",
            "workspaces",
            "active_workspace",
            "privacy_referrer_policy",
            "privacy_dns_prefetch",
        ):
            self.assertIn(key, DEFAULT_SETTINGS)


class GuiTests(unittest.TestCase):
    """Pruebas que necesitan QApplication (offscreen en CI)."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
        cls._tmp = tempfile.TemporaryDirectory(prefix="pedrozilla-tests-")
        os.environ["XDG_CONFIG_HOME"] = cls._tmp.name
        os.environ["XDG_DATA_HOME"] = cls._tmp.name

        from PySide6.QtWidgets import QApplication

        cls.app = QApplication.instance() or QApplication([])

        from pedrozilla.browser import BrowserContext, BrowserWindow
        from pedrozilla.storage import Bookmarks, History, Settings

        cls.ctx = BrowserContext(Settings(), History(), Bookmarks())
        cls.profile = cls.ctx.build_persistent_profile()
        cls.window = BrowserWindow(cls.ctx, cls.profile)
        cls.window.new_tab(focus=False)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls._tmp.cleanup()

    def test_no_duplicate_keyboard_shortcuts(self) -> None:
        from PySide6.QtGui import QAction

        shortcuts: dict[str, list[str]] = defaultdict(list)
        for action in self.window.findChildren(QAction):
            sequence = action.shortcut().toString()
            if sequence:
                shortcuts[sequence].append(action.text())
        duplicates = {key: value for key, value in shortcuts.items() if len(value) > 1}
        self.assertEqual(duplicates, {})

    def test_settings_dialog_categories_and_values(self) -> None:
        from pedrozilla.dialogs import SettingsDialog
        from pedrozilla.storage import DEFAULT_SETTINGS

        dialog = SettingsDialog(self.ctx.settings, None, clear_data=lambda: None)
        self.assertEqual(dialog.category_list.count(), 11)
        self.assertEqual(dialog.pages.count(), 11)
        dialog.search_box.setText("tema")
        visible = [
            dialog.category_list.item(i).text()
            for i in range(dialog.category_list.count())
            if not dialog.category_list.item(i).isHidden()
        ]
        self.assertIn("Apariencia", visible)
        dialog.search_box.clear()
        values = dialog.values()
        for key in (
            "reader_font_size",
            "privacy_referrer_policy",
            "privacy_dns_prefetch",
            "javascript",
        ):
            self.assertIn(key, values)
        dialog._reset_defaults()
        self.assertEqual(dialog.theme.currentData(), DEFAULT_SETTINGS["theme"])
        self.assertEqual(
            dialog.referrer_policy.currentData(), DEFAULT_SETTINGS["privacy_referrer_policy"]
        )

    def test_privacy_dialog(self) -> None:
        from pedrozilla.dialogs import PrivacyDialog

        dialog = PrivacyDialog(
            self.profile, self.ctx.settings, "https://example.com", "", None
        )
        self.assertEqual(dialog.windowTitle(), "Centro de privacidad")
        self.assertEqual(dialog.perm_rows, [])

    def test_groups_collapse_and_split_view(self) -> None:
        from pedrozilla.browser import SplitView

        self.window.new_tab(focus=False)
        self.window.tab_groups["test-group"] = {
            "name": "Prueba",
            "color": "verde",
            "collapsed": False,
        }
        index = self.window.tabs.currentIndex()
        self.window._assign_group(index, "test-group")
        self.assertIn("🟢", self.window.tabs.tabText(index))
        self.window._toggle_group_collapse("test-group")
        self.assertFalse(self.window.tabs.tabBar().isTabVisible(index))
        self.window._toggle_group_collapse("test-group")
        self.assertTrue(self.window.tabs.tabBar().isTabVisible(index))

        self.window.toggle_split_view()
        container = self.window.tabs.widget(self.window.tabs.currentIndex())
        self.assertIsInstance(container, SplitView)
        self.assertEqual(len(container.views), 2)
        self.assertIsNot(container.views[0].page(), container.views[1].page())
        self.window.toggle_split_view()
        self.assertNotIsInstance(
            self.window.tabs.widget(self.window.tabs.currentIndex()), SplitView
        )
        self.window._delete_group("test-group")

    def test_hidden_menubar_and_main_menu_actions(self) -> None:
        from PySide6.QtGui import QAction

        from pedrozilla.icons import menu_icon

        self.assertFalse(menu_icon("Nueva pestaña").isNull())
        self.assertFalse(self.window.menuBar().isVisible())
        self.assertEqual(self.window.menuBar().actions(), [])
        self.assertEqual(self.window.action_menu.text(), "☰")
        self.assertNotEqual(self.window._menu_button.objectName(), "MenuButton")

        menu = self.window._build_main_menu()
        self.assertEqual(menu.objectName(), "PedrozillaMainMenu")
        self.assertLessEqual(menu.tree.maximumHeight(), 560)
        self.assertGreater(menu.tree.verticalScrollBar().maximum(), 0)

        entries = self.window._main_menu_entries()
        self.assertEqual(menu.tree.topLevelItemCount(), len(entries))
        sections = [entry.text for entry in entries if entry.kind == "section"]
        self.assertEqual(
            sections,
            [
                "ARCHIVO",
                "EDITAR",
                "VER",
                "HISTORIAL",
                "MARCADORES",
                "DESCARGAS",
                "HERRAMIENTAS",
                "AYUDA",
            ],
        )
        actions = [entry.action for entry in entries if entry.kind == "action"]
        labels = [self.window._action_key(entry.text) for entry in entries]
        for expected in (
            "Nueva pestaña",
            "Recargar sin caché",
            "Ver historial",
            "Añadir marcador",
            "Abrir carpeta de descargas",
            "Privacidad y seguridad",
            "Acerca de Pedrozilla",
        ):
            self.assertIn(expected, labels)
        self.assertTrue(all(action is not None and action.isEnabled() for action in actions))
        self.assertTrue(all(not action.icon().isNull() for action in actions))
        self.assertIn("Ctrl+T", [action.shortcut().toString() for action in actions])
        self.assertTrue(any(entry.kind == "submenu" for entry in entries))

    def test_workspaces_switch(self) -> None:
        # Instantáneas explícitas y un espacio "scratch": el resultado no
        # depende del orden en que unittest ejecute las pruebas.
        self.window.workspaces["test-a"] = {
            "name": "A",
            "color": "rojo",
            "tabs": [{"url": ""}],
            "groups": {},
            "active": 0,
        }
        self.window.workspaces["test-b"] = {
            "name": "B",
            "color": "azul",
            "tabs": [{"url": ""}, {"url": ""}],
            "groups": {},
            "active": 0,
        }
        self.window.active_workspace = "scratch"
        self.window.switch_workspace("test-b")
        self.assertEqual(self.window.tabs.count(), 2)
        self.window.switch_workspace("test-a")
        self.assertEqual(self.window.tabs.count(), 1)
        self.window.switch_workspace("test-b")
        self.assertEqual(self.window.tabs.count(), 2)


if __name__ == "__main__":
    unittest.main()
