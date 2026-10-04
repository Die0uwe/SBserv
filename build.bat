@echo off
REM Bouwt sbserv.exe (geen Python nodig voor eindgebruikers) + haalt cloudflared.exe op
REM en compileert daarna de installer. Vereist: Python 3 + Inno Setup 6 (iscc.exe).
setlocal
cd /d "%~dp0"

echo [1/4] PyInstaller installeren/bijwerken...
python -m pip install --upgrade pyinstaller || goto :fail

echo [2/4] sbserv.exe bouwen...
python -m PyInstaller --onefile --console --name sbserv --icon assets\favicon.ico --add-data "assets;assets" --clean sbserv.py || goto :fail

echo [3/4] cloudflared.exe ophalen (officiele Cloudflare release)...
if not exist cloudflared.exe (
  curl -L --fail -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe || (
    echo Waarschuwing: download mislukt. De installer werkt nog; het programma downloadt zelf later.
    del cloudflared.exe 2>nul
  )
)

echo [4/4] Installer compileren...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
%ISCC% sbserv_installer.iss || goto :fail

echo Klaar: SBserv_Setup_v1.0.exe
exit /b 0
:fail
echo MISLUKT.
exit /b 1
