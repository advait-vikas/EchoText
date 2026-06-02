; EchoText Installer Script - Inno Setup 6
; Packages the EchoText Electron app (from electron-builder win-unpacked) into a single Setup.exe

[Setup]
AppId={{C0E2B7E1-8B2A-4B1A-9C1A-1A2B3C4D5E6F}
AppName=EchoText
AppVersion=1.0.0
AppPublisher=EchoText
AppPublisherURL=https://echotext.app
AppSupportURL=https://echotext.app
AppUpdatesURL=https://echotext.app
DefaultDirName={autopf}\EchoText
DefaultGroupName=EchoText
AllowNoIcons=yes
OutputDir=C:\Users\advai\Desktop\Code\text_to_voice\release
OutputBaseFilename=EchoText_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\EchoText.exe
DisableProgramGroupPage=yes
LicenseFile=
; Minimum Windows version: Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Bundle entire win-unpacked folder (includes Electron + backend + frontend)
Source: "C:\Users\advai\Desktop\Code\text_to_voice\release\win-unpacked\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\EchoText"; Filename: "{app}\EchoText.exe"
Name: "{autodesktop}\EchoText"; Filename: "{app}\EchoText.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EchoText.exe"; \
    Description: "{cm:LaunchProgram,EchoText}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up AppData folder on uninstall
Type: filesandordirs; Name: "{userappdata}\EchoText"
