; ============================================================================
; SBserv Installer Script  -  Inno Setup 6.3 of nieuwer (donker thema vanaf 6.6.0)
; ============================================================================
; Zo gebruik je het:
;   * Alles-in-een-map: dubbelklik make_kit.bat. Dat bouwt sbserv.exe, haalt
;     cloudflared.exe op, zet ALLES (exe, logo, iconen, README, info-teksten,
;     dit script) in de map SBserv_kit\ en compileert daar de installer.
;   * Heb je al een sbserv.exe? Zet hem naast dit bestand (of in dist\), open
;     dit bestand in Inno Setup en druk Ctrl+F9, of dubbelklik installer.bat.
;   * Zonder sbserv.exe valt het script terug op sbserv.py (Python nodig).
; Resultaat: SBserv_Setup_v<versie>.exe naast dit bestand.
;
; Mappen die dit script verwacht (naast het .iss):
;   sbserv.exe  (of dist\sbserv.exe)   cloudflared.exe (optioneel)
;   assets\     logo, favicon, installerplaatjes, startpagina, dashboard, lang\
;   installer\  info_before_*.txt (voor de installatie), info_after_*.txt (erna)
;   README.md, CHANGELOG.md            LICENSE.txt (optioneel: licentiepagina)
; ============================================================================

#define MyAppName "SBserv"
#define MyAppVersion "1.1"
#define MyAppPublisher "Scriptspace"
#define MyAppURL "http://scriptspace.nl"

#ifexist "dist\sbserv.exe"
  #define UseExe
  #define ExeSrc "dist\sbserv.exe"
#else
  #ifexist "sbserv.exe"
    #define UseExe
    #define ExeSrc "sbserv.exe"
  #endif
#endif
#ifdef UseExe
  #define MyAppExeName "sbserv.exe"
#else
  #define MyAppExeName "sbserv.py"
#endif

[Setup]
AppId={{9C4B3E2A-1F5E-4C23-9B3F-56789ABC1234}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppComments=Standalone web server with SQLite database
AppCopyright=Copyright (C) Scriptspace
DefaultDirName=C:\SERVERS\SBserv
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
OutputDir=.
OutputBaseFilename=SBserv_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
#if Ver >= 0x06060000
; Donkere installer (Inno Setup 6.6.0 of nieuwer). Liever meebewegen met Windows? Zet "dark" op "dynamic".
WizardStyle=modern dark
#else
WizardStyle=modern
#endif
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes
; Een draaiende versie wordt in [Code] gestopt zodat updaten niet faalt op vergrendelde bestanden
CloseApplications=yes
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoDescription={#MyAppName} Setup
; Logo & afbeeldingen (uit assets\): app-icoon, grote zijbalk en klein kopplaatje, meerdere DPI-formaten
SetupIconFile=assets\favicon.ico
UninstallDisplayIcon={app}\assets\favicon.ico
WizardImageFile=assets\wizard_164x314.bmp,assets\wizard_246x459.bmp
WizardSmallImageFile=assets\wizard_small_55.bmp,assets\wizard_small_83.bmp,assets\wizard_small_110.bmp
; Taalkeuze tonen bij start van de installer (Engels / Nederlands)
ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage
#ifexist "LICENSE.txt"
; Licentiepagina verschijnt alleen als LICENSE.txt naast dit script staat
LicenseFile=LICENSE.txt
#endif

[Languages]
; Let op: "Dutchduc.isl" bestaat niet - de juiste naam is Dutch.isl
; InfoBeforeFile = pagina VOOR de installatie, InfoAfterFile = pagina NA de installatie
Name: "english"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "installer\info_before_en.txt"; InfoAfterFile: "installer\info_after_en.txt"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"; InfoBeforeFile: "installer\info_before_nl.txt"; InfoAfterFile: "installer\info_after_nl.txt"

[CustomMessages]
english.NoPython=Python was not found on this PC.%nInstall Python 3 (python.org, tick "Add to PATH") or use the installer with the built-in .exe.
dutch.NoPython=Python is niet gevonden op deze pc.%nInstalleer Python 3 (python.org, vink "Add to PATH" aan) of gebruik de installer met ingebouwde .exe.
english.IconFolder=SBserv website folder
dutch.IconFolder=SBserv websitemap
english.OpenFolder=Open the website folder
dutch.OpenFolder=Open de websitemap
english.KeepData=Do you want to KEEP your data (database, settings and your website files in public_html)?%n%nYes = keep (recommended, handy when you install again later)%nNo = delete everything
dutch.KeepData=Wil je je gegevens BEWAREN (database, instellingen en je websitebestanden in public_html)?%n%nJa = bewaren (aanbevolen, handig als je later opnieuw installeert)%nNee = alles verwijderen

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
#ifdef UseExe
Source: "{#ExeSrc}"; DestDir: "{app}"; Flags: ignoreversion
#else
Source: "sbserv.py"; DestDir: "{app}"; Flags: ignoreversion
#endif
; Logo, favicon, installerplaatjes, startpagina, dashboard en vertalingen (assets\lang\*.json) - bewerkbaar zonder opnieuw te bouwen
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "source\*,*.bmp"
; Documentatie
Source: "README.md"; DestDir: "{app}\docs"; Flags: ignoreversion skipifsourcedoesntexist
Source: "CHANGELOG.md"; DestDir: "{app}\docs"; Flags: ignoreversion skipifsourcedoesntexist
; Voorbeeldsite: alleen plaatsen als gebruiker nog niets heeft (nooit eigen werk overschrijven)
Source: "public_html\*"; DestDir: "{app}\public_html"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs skipifsourcedoesntexist
; cloudflared meeleveren als hij naast dit script ligt (make_kit.bat / build.bat haalt hem op).
; Ontbreekt hij, dan downloadt het programma hem zelf bij de eerste tunnel.
Source: "cloudflared.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Dirs]
; Schrijfbaar voor gewone gebruikers, zodat database/config altijd kunnen worden opgeslagen
Name: "{app}"; Permissions: users-modify

[Icons]
#ifdef UseExe
Name: "{group}\{#MyAppName}"; Filename: "{app}\sbserv.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\favicon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\sbserv.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\favicon.ico"; Tasks: desktopicon
#else
Name: "{group}\{#MyAppName}"; Filename: "python.exe"; Parameters: """{app}\sbserv.py"""; WorkingDir: "{app}"; IconFilename: "{app}\assets\favicon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "python.exe"; Parameters: """{app}\sbserv.py"""; WorkingDir: "{app}"; IconFilename: "{app}\assets\favicon.ico"; Tasks: desktopicon
#endif
Name: "{group}\{cm:IconFolder}"; Filename: "{app}\public_html"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Run]
#ifdef UseExe
Filename: "{app}\sbserv.exe"; Parameters: "--lang {language}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
#else
Filename: "python.exe"; Parameters: """{app}\sbserv.py"" --lang {language}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
#endif
Filename: "{app}\public_html"; Description: "{cm:OpenFolder}"; Flags: postinstall shellexec skipifsilent unchecked

; Bewust GEEN [UninstallDelete] voor database.db, public_html en config.json:
; die vraagt de uninstaller apart (zie [Code]). Alleen de gedownloade tunnel-binary en vertalingen mogen altijd weg.
[UninstallDelete]
Type: filesandordirs; Name: "{app}\bin"
Type: filesandordirs; Name: "{app}\lang"
Type: filesandordirs; Name: "{app}\docs"

[Code]
// Stopt een draaiende SBserv (en de tunnel die hij gestart heeft) zodat bestanden niet vergrendeld zijn.
procedure StopRunningApp();
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM sbserv.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeSetup(): Boolean;
#ifndef UseExe
var
  ResultCode: Integer;
#endif
begin
  Result := True;
#ifndef UseExe
  if not Exec('python.exe', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
  begin
    MsgBox(CustomMessage('NoPython'), mbError, MB_OK);
    Result := False;
  end;
#endif
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  StopRunningApp();
  Result := '';
end;

function InitializeUninstall(): Boolean;
begin
  StopRunningApp();
  Result := True;
end;

// Na het verwijderen: vraag of de gebruikersdata (database, config, public_html) mag blijven.
// Bij een stille uninstall (/SILENT) blijft alles staan.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if (not UninstallSilent) and DirExists(ExpandConstant('{app}')) then
    begin
      if MsgBox(CustomMessage('KeepData'), mbConfirmation, MB_YESNO or MB_DEFBUTTON1) = IDNO then
        DelTree(ExpandConstant('{app}'), True, True, True);
    end;
  end;
end;
