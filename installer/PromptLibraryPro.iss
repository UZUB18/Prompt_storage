; Inno Setup script for Prompt Library Pro (PyInstaller onedir build)
; Build first: .\build_windows.ps1 -Mode onedir

#define AppName "Prompt Library Pro"
#define AppExeName "PromptLibraryPro.exe"
#define AppPublisher "UZUB18"
#define AppURL "https://github.com/UZUB18/Prompt_storage"

; Allow CI to override version: ISCC.exe /DMyAppVersion=0.1.0 installer\PromptLibraryPro.iss
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif

[Setup]
AppId={{8E91829D-7F33-4B65-A4B7-5A7D3D7AB6A2}
AppName={#AppName}
AppVersion={#MyAppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Per-user install (no admin needed), still shows in Start Menu / Windows Search
DefaultDirName={localappdata}\Programs\PromptLibraryPro
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

OutputDir=..\dist-installer
OutputBaseFilename=PromptLibraryProSetup
Compression=lzma
SolidCompression=yes

WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}
SetupIconFile=..\prompt_library.ico

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\PromptLibraryPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
