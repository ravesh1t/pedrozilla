; Instalador de Pedrozilla para Windows (NSIS).
; Lo genera crear_setup.bat a partir de dist\Pedrozilla\ (crear_exe.bat).
; Se instala en %LOCALAPPDATA%\Pedrozilla: no pide Python, ni admin.
; Los datos del usuario (%APPDATA%\pedrozilla) no se tocan ni al desinstalar.

!include "MUI2.nsh"

Name "Pedrozilla"
OutFile "${__FILEDIR__}\..\dist\PedrozillaSetup-1.0.2.exe"
InstallDir "$LOCALAPPDATA\Pedrozilla"
RequestExecutionLevel user
Icon "${__FILEDIR__}\..\pedrozilla\pedrozilla.ico"
UninstallIcon "${__FILEDIR__}\..\pedrozilla\pedrozilla.ico"

VIProductVersion "1.0.2.0"
VIAddVersionKey "ProductName" "Pedrozilla"
VIAddVersionKey "FileVersion" "1.0.2"
VIAddVersionKey "ProductVersion" "1.0.2"
VIAddVersionKey "CompanyName" "Pedrozilla"
VIAddVersionKey "LegalCopyright" "Pedrozilla (MIT)"
VIAddVersionKey "FileDescription" "Instalador de Pedrozilla"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Spanish"

Section "Pedrozilla" SecMain
  SetOutPath "$INSTDIR"
  File /r "${__FILEDIR__}\..\dist\Pedrozilla\*"

  CreateDirectory "$SMPROGRAMS\Pedrozilla"
  CreateShortcut "$SMPROGRAMS\Pedrozilla\Pedrozilla.lnk" "$INSTDIR\Pedrozilla.exe" "" "$INSTDIR\Pedrozilla.exe" 0
  CreateShortcut "$SMPROGRAMS\Pedrozilla\Pedrozilla (privada).lnk" "$INSTDIR\Pedrozilla.exe" "--incognito" "$INSTDIR\Pedrozilla.exe" 0
  CreateShortcut "$SMPROGRAMS\Pedrozilla\Desinstalar Pedrozilla.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  CreateShortcut "$DESKTOP\Pedrozilla.lnk" "$INSTDIR\Pedrozilla.exe" "" "$INSTDIR\Pedrozilla.exe" 0

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "DisplayName" "Pedrozilla"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "DisplayVersion" "1.0.2"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "Publisher" "Pedrozilla"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "DisplayIcon" "$INSTDIR\Pedrozilla.exe"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Pedrozilla.lnk"
  RMDir /r "$SMPROGRAMS\Pedrozilla"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pedrozilla"
SectionEnd
