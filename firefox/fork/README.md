# Pedrozilla como navegador aparte: fork compilado de Firefox (Gecko)

La 2.x reutiliza el Firefox instalado con otro perfil. Eso vale como
distribución ligera, pero **no es una aplicación separada**: la ventana, el
motor y la identidad de la app siguen siendo Firefox.

Un navegador aparte con Gecko solo existe **compilando un fork**, como hacen
Waterfox, LibreWolf o Floorp: fuente de Firefox + marca propia + compilación
propia. Esta carpeta contiene todo lo específico de Pedrozilla para eso; el
fuente de Mozilla (GBs) **no** se sube al repo.

## Estado

- [x] mozconfig de marca propia (`fork/mozconfig`)
- [x] Script de compilación (`fork/build.ps1`)
- [x] Branding `pedrozilla/` validado contra el fuente 156 (nombres, prefs,
      iconos desde `assets/pedrozilla.ico`, logos, instalador, MSIX)
- [ ] Toolchain instalado (VS 2022 + bootstrap)
- [ ] Primera compilación `mach build` + `mach package`

## Requisitos (una vez)

- Windows 10/11 64 bits, ~50 GB libres (hay 132 GB en `D:`), 8 GB de RAM o más.
- Visual Studio 2022 Community (lo instala `fork/build.ps1` con winget).
- Conexión para descargar el fuente (~769 MB) y el toolchain.

## Paso 1 — descargar el fuente (ya en marcha)

```powershell
# D:\mozilla\firefox-156.0.1.source.tar.xz  (769 MB, archive.mozilla.org)
```

Descomprimir en `D:\mozilla\firefox-156.0.1` de modo que exista
`D:\mozilla\firefox-156.0.1\browser\branding\official`.

## Paso 2 — branding Pedrozilla

`fork/branding/pedrozilla/` se copia a `browser/branding/pedrozilla/` del
fuente y `mozconfig` lo activa con `--with-branding`. Contiene nombre de la
aplicación, textos legales y los iconos (se reutiliza `assets/pedrozilla.ico`
como base del `.ico` de la app).

## Paso 3 — compilar

```powershell
.\fork\build.ps1
```

Hace: comprobar VS → `mach bootstrap` → `mach build` → `mach package`.
La compilación tarda **horas** en un 6 núcleos; es normal.

## Notas honestas

- Cada versión nueva de Firefox exige rebase del fork y recompilar: el coste
  de mantenimiento es real (por eso los forks siguen ESR o releases).
- La primera versión sale **sin actualizador propio** (`--disable-updater`):
  se distribuye el instalador/zip generado por `mach package`.
- El perfil de la 2.x (`%APPDATA%\pedrozilla\firefox-profile`) sirve igual
  para el fork: mismo formato de perfil, misma migración de marcadores.
