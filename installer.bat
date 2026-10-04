@echo off
REM Maakt alleen de installer (SBserv_Setup_v1.1.exe) van een bestaande sbserv.exe.
REM Zet sbserv.exe naast dit bestand of in de map dist\. Vereist: Inno Setup 6.3 of nieuwer.
setlocal
cd /d "%~dp0"

if not exist "dist\sbserv.exe" if not exist "sbserv.exe" (
  echo sbserv.exe niet gevonden. Zet hem naast dit bestand of in de map dist\, of draai build.bat.
  exit /b 1
)

if not exist cloudflared.exe (
  echo cloudflared.exe ophalen...
  curl -L --fail -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe || (
    echo Waarschuwing: download mislukt. De installer werkt nog; het programma downloadt hem zelf later.
    del cloudflared.exe 2>nul
  )
)

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo Inno Setup 6 niet gevonden. Installeer het van https://jrsoftware.org/isinfo.php
  exit /b 1
)

%ISCC% sbserv_installer.iss || (echo MISLUKT. & exit /b 1)
echo Klaar: SBserv_Setup_v1.1.exe
