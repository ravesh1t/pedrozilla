"""Permite ejecutar el navegador con `python3 -m pedrozilla`."""

import sys


def _run() -> int:
    try:
        from .main import main
    except ModuleNotFoundError as exc:
        # No comprobamos la dependencia en run.sh con un Python extra: eso
        # duplicaba el arranque. Si falta, aquí se explica con claridad.
        if (exc.name or "").split(".")[0] == "PySide6":
            print(
                "Falta PySide6 con Qt WebEngine.\n"
                "Instálalo con:\n  python3 -m pip install --user PySide6",
                file=sys.stderr,
            )
            return 1
        raise
    return main()


if __name__ == "__main__":
    raise SystemExit(_run())
