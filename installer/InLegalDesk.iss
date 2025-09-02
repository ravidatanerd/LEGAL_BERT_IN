; InLegalDesk Windows Installer Script for Inno Setup
; This script creates a Windows installer for the InLegalDesk application

#define MyAppName "InLegalDesk"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Legal AI Solutions"
#define MyAppURL "https://github.com/example/inlegaldesk"
#define MyAppExeName "InLegalDesk.exe"
#define MyAppDescription "AI-powered Legal Research and Judgment Drafting System"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=README.txt
OutputDir=output
OutputBaseFilename={#MyAppName}_Installer
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Minimum Windows version
MinVersion=6.1sp1

; Uninstall information
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Main application executable
Source: "..\dist\InLegalDesk\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\InLegalDesk\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Backend server files
Source: "..\app.py"; DestDir: "{app}\server"; Flags: ignoreversion
Source: "..\ingest.py"; DestDir: "{app}\server"; Flags: ignoreversion
Source: "..\retriever.py"; DestDir: "{app}\server"; Flags: ignoreversion
Source: "..\llm.py"; DestDir: "{app}\server"; Flags: ignoreversion
Source: "..\chunking.py"; DestDir: "{app}\server"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}\server"; Flags: ignoreversion

; Backend utility modules
Source: "..\utils\*"; DestDir: "{app}\server\utils"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\extractors\*"; DestDir: "{app}\server\extractors"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\sources\*"; DestDir: "{app}\server\sources"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration files
Source: "..\.env.sample"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\desktop\.env.sample"; DestDir: "{app}"; Flags: ignoreversion; DestName: ".env.sample"

; Documentation
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\temp"

[Code]
// Custom code for installer
procedure InitializeWizard();
begin
  // Custom initialization code can go here
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Check if Python is installed (optional check)
  // This is just informational since we're providing a standalone executable
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation tasks
    // Create necessary directories
    CreateDir(ExpandConstant('{app}\data'));
    CreateDir(ExpandConstant('{app}\data\documents'));
    CreateDir(ExpandConstant('{app}\data\chunks'));
    CreateDir(ExpandConstant('{app}\data\downloads'));
    CreateDir(ExpandConstant('{app}\logs'));
    CreateDir(ExpandConstant('{app}\temp'));
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Post-uninstall cleanup
    // Remove any remaining user data if desired
  end;
end;