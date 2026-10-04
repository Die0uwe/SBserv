@echo off
REM Maakt de map SBserv_kit\ met ALLES voor Inno Setup op een rij:
REM   sbserv.exe, cloudflared.exe, logo/iconen/installerplaatjes (assets\), README, CHANGELOG,
REM   info-teksten voor en na de installatie (installer\) en het Inno-script - en compileert
REM   daar de installer: SBserv_kit\SBserv_Setup_v1.1.exe
REM Gebruik:  make_kit.bat            bouwt sbserv.exe opnieuw (aanbevolen na elke wijziging)
REM           make_kit.bat norebuild  hergebruikt dist\sbserv.exe als die er al is
REM Vereist: Python 3 (in PATH) en Inno Setup 6.3 of nieuwer.
setlocal
cd /d "%~dp0"
set "KIT=%~dp0SBserv_kit"

if /i "%~1"=="norebuild" if exist "dist\sbserv.exe" goto :tunnel

echo [1/5] sbserv.exe bouwen...
python -m pip install --upgrade pyinstaller || goto :fail
python -m PyInstaller --onefile --console --name sbserv --icon assets\favicon.ico --add-data "assets;assets" --clean sbserv.py || goto :fail

:tunnel
echo [2/5] cloudflared.exe (officiele Cloudflare release)...
if not exist cloudflared.exe (
  curl -L --fail -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe || (
    echo Waarschuwing: download mislukt. De installer werkt nog; het programma downloadt hem zelf later.
    del cloudflared.exe 2>nul
  )
)

echo [3/5] Map SBserv_kit samenstellen...
if exist "%KIT%" rmdir /s /q "%KIT%"
mkdir "%KIT%" || goto :fail
copy /y dist\sbserv.exe "%KIT%\" >nul || goto :fail
if exist cloudflared.exe copy /y cloudflared.exe "%KIT%\" >nul
copy /y sbserv_installer.iss "%KIT%\" >nul || goto :fail
copy /y installer.bat "%KIT%\" >nul
copy /y README.md "%KIT%\" >nul
copy /y CHANGELOG.md "%KIT%\" >nul
if exist LICENSE.txt copy /y LICENSE.txt "%KIT%\" >nul
xcopy /e /i /y /q assets "%KIT%\assets" >nul || goto :fail
xcopy /e /i /y /q installer "%KIT%\installer" >nul || goto :fail

echo [4/5] Installer compileren (Inno Setup)...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo Inno Setup 6 niet gevonden. Installeer het van https://jrsoftware.org/isinfo.php
  echo De map SBserv_kit is wel klaar: open daar sbserv_installer.iss in Inno Setup en druk Ctrl+F9.
  exit /b 1
)
pushd "%KIT%"
%ISCC% sbserv_installer.iss || (popd & goto :fail)
popd

echo [5/5] Klaar. Inhoud van SBserv_kit:
dir /b "%KIT%"
echo.
echo Installer: %KIT%\SBserv_Setup_v1.1.exe
exit /b 0
:fail
echo MISLUKT.
exit /b 1
