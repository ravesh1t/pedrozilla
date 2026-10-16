#!/usr/bin/env python3
"""Punto de entrada de Pedrozilla.

Uso:
    python3 -m pedrozilla [opciones] [URL ...]

Opciones:
    --incognito       abre una ventana privada
    --debug           muestra los mensajes de la consola JavaScript
"""

from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from . import __version__
from .browser import BrowserContext, apply_theme, brand_icon
from .storage import Bookmarks, History, Settings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pedrozilla",
        description="Navegador de escritorio basado en Chromium (Qt WebEngine).",
    )
    parser.add_argument("urls", nargs="*", help="URLs o búsquedas a abrir al arrancar")
    parser.add_argument("--incognito", "-i", action="store_true", help="abrir una ventana privada")
    parser.add_argument("--debug", action="store_true", help="mostrar la consola JavaScript")
    parser.add_argument("--version", action="version", version=f"Pedrozilla {__version__}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))

    # Debe fijarse antes de crear QApplication para que WebEngine comparta el contexto GL.
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QGuiApplication.setApplicationName("Pedrozilla")
    QGuiApplication.setApplicationDisplayName("Pedrozilla")
    QGuiApplication.setOrganizationName("Pedrozilla")
    QGuiApplication.setApplicationVersion(__version__)
    # Asocia la ventana con pedrozilla.desktop para que el escritorio use su icono.
    QGuiApplication.setDesktopFileName("pedrozilla")

    app = QApplication([sys.argv[0]] if argv is None else [sys.argv[0], *argv])
    app.setWindowIcon(brand_icon(128))
    app.setApplicationName("Pedrozilla")
    app.setQuitOnLastWindowClosed(True)

    settings = Settings(app)
    history = History(app)
    bookmarks = Bookmarks(app)

    apply_theme(app, settings.get("theme", "classic"))

    context = BrowserContext(settings, history, bookmarks)
    context.build_persistent_profile()

    urls = [url for url in args.urls if url]
    if args.incognito:
        window = context.open_window(incognito=True, urls=urls)
    else:
        window = context.open_window(urls=urls)
    window.debug_console = bool(args.debug)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
