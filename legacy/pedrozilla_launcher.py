"""Punto de entrada para empaquetar Pedrozilla con PyInstaller.

El navegador se ejecuta normalmente con `python -m pedrozilla`; este archivo
existe solo para darle a PyInstaller un script de arranque (no admite `-m`).
Lo usa `crear_exe.bat`.
"""

from pedrozilla.main import main

if __name__ == "__main__":
    raise SystemExit(main())
