; SBserv Installer Script
; Gemaakt voor Inno Setup 6.x
; Bouwen: eerst build.bat draaien (maakt sbserv.exe + haalt cloudflared.exe op),
; daarna dit script compileren in Inno Setup.
; Zonder build.bat valt het terug op sbserv.py (dan is Python op de pc nodig).

#define MyAppName "SBserv"
#define MyAppVersion "1.0"
#define MyAppPublisher "Scriptspace"
#define MyAppURL "http://scriptspace.nl"

#ifexist "dist\sbserv.exe"
  #define UseExe
  #define MyAppExeName "sbserv.exe"
#else
  #define MyAppExeName "sbserv.py"
#endif

[Setup]
AppId={{9C4B3E2A-1F5E-4C23-9B3F-56789ABC1234}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName=C:\SERVERS\SBserv
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
OutputDir=.
OutputBaseFilename=SBserv_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Sluit een draaiende versie af zodat updaten niet faalt op vergrendelde bestanden
CloseApplications=yes
UninstallDisplayName={#MyAppName}
; Logo & afbeeldingen (uit assets\): app-icoon, grote zijbalk en klein kopplaatje, meerdere DPI-formaten
SetupIconFile=assets\favicon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardImageFile=assets\wizard_164x314.bmp,assets\wizard_246x459.bmp
WizardSmallImageFile=assets\wizard_small_55.bmp,assets\wizard_small_83.bmp,assets\wizard_small_110.bmp
; Taalkeuze tonen bij start van de installer (Engels / Nederlands)
ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage

[Languages]
; Let op: "Dutchduc.isl" bestaat niet - de juiste naam is Dutch.isl
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"

[CustomMessages]
english.NoPython=Python was not found on this PC.%nInstall Python 3 (python.org, tick "Add to PATH") or use the installer with the built-in .exe.
dutch.NoPython=Python is niet gevonden op deze pc.%nInstalleer Python 3 (python.org, vink "Add to PATH" aan) of gebruik de installer met ingebouwde .exe.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
#ifdef UseExe
Source: "dist\sbserv.exe"; DestDir: "{app}"; Flags: ignoreversion
#else
Source: "sbserv.py"; DestDir: "{app}"; Flags: ignoreversion
#endif
; Logo, favicon, installerplaatjes en vertalingen (assets\lang\*.json) - bewerkbaar zonder opnieuw te bouwen
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "source\*,*.bmp"
; Voorbeeldsite: alleen plaatsen als gebruiker nog niets heeft (nooit eigen werk overschrijven)
Source: "public_html\*"; DestDir: "{app}\public_html"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs skipifsourcedoesntexist
; cloudflared meeleveren als hij naast dit script ligt (build.bat haalt hem op).
; Ontbreekt hij, dan downloadt het programma hem zelf bij de eerste tunnel.
Source: "cloudflared.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Dirs]
; Schrijfbaar voor gewone gebruikers, zodat database/config altijd kunnen worden opgeslagen
Name: "{app}"; Permissions: users-modify

[Icons]
#ifdef UseExe
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\sbserv.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\sbserv.exe"; WorkingDir: "{app}"; Tasks: desktopicon
#else
Name: "{autoprograms}\{#MyAppName}"; Filename: "python.exe"; Parameters: """{app}\sbserv.py"""; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "python.exe"; Parameters: """{app}\sbserv.py"""; WorkingDir: "{app}"; Tasks: desktopicon
#endif

[Run]
#ifdef UseExe
Filename: "{app}\sbserv.exe"; Parameters: "--lang {language}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
#else
Filename: "python.exe"; Parameters: """{app}\sbserv.py"" --lang {language}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
#endif

; Bewust GEEN [UninstallDelete] voor database.db, public_html en config.json:
; gebruikersdata blijft bij verwijderen behouden. Alleen de gedownloade tunnel-binary mag weg.
[UninstallDelete]
Type: filesandordirs; Name: "{app}\bin"
Type: filesandordirs; Name: "{app}\lang"

#ifndef UseExe
[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if not Exec('python.exe', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
  begin
    MsgBox(CustomMessage('NoPython'), mbError, MB_OK);
    Result := False;
  end;
end;
#endif
