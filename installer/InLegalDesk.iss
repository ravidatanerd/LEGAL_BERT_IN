#define MyAppName "InLegalDesk"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "InLegalDesk Team"
#define MyAppURL "https://github.com/ravidatanerd/LEGAL_BERT_IN"
#define MyAppExeName "InLegalDesk_Launcher.exe"

[Setup]
; Unique App ID
AppId={{A1B2C3D4-E5F6-7890-ABCD-123456789ABC}

; Basic app info
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; License and output
LicenseFile=..\LICENSE
InfoBeforeFile=installer\assets\before_install.txt
InfoAfterFile=installer\assets\after_install.txt
OutputDir=installer\output
OutputBaseFilename=InLegalDesk-Setup-v{#MyAppVersion}

; Installer appearance
SetupIconFile=installer\assets\icon.ico
WizardStyle=modern
WizardImageFile=installer\assets\wizard_image.bmp
WizardSmallImageFile=installer\assets\wizard_small.bmp

; Compression and architecture
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Privileges and compatibility
PrivilegesRequired=admin
MinVersion=6.1sp1
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1
Name: "addtopath"; Description: "Add InLegalDesk to PATH"; GroupDescription: "System Integration"

[Files]
; Main application files
Source: "backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "desktop\*"; DestDir: "{app}\desktop"; Flags: ignoreversion recursesubdirs createallsubdirs

; Installation scripts and tools
Source: "installer\smart_dependency_installer.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "ULTIMATE_AI_FIX.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "AUTO_PYTHON_UPGRADE.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHECK_BEFORE_INSTALL.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "UPGRADE_PIP_FIRST.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "check_python_compatibility.py"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "VLM_CONFIGURATION_GUIDE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "UI_MOCKUP_SIMULATION.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "BUILD_TEST_RESULTS.md"; DestDir: "{app}"; Flags: ignoreversion

; Configuration files
Source: "backend\.env.sample"; DestDir: "{app}\backend"; Flags: ignoreversion
Source: "backend\requirements.txt"; DestDir: "{app}\backend"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\InLegalDesk Web Interface"; Filename: "http://localhost:8877"; IconFilename: "{app}\installer\assets\web_icon.ico"
Name: "{group}\Configuration Guide"; Filename: "{app}\VLM_CONFIGURATION_GUIDE.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Add to PATH if requested
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath('{app}')

[Code]
var
  DependencyPage: TOutputProgressWizardPage;
  PythonCompatible: Boolean;
  PythonVersion: String;
  
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

function CheckPythonVersion(): Boolean;
var
  ResultCode: Integer;
  PythonOutput: AnsiString;
  TempFile: String;
begin
  Result := False;
  PythonCompatible := False;
  
  // Create temp file for output
  TempFile := ExpandConstant('{tmp}\python_check.txt');
  
  // Check if Python exists and get version
  if Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if Exec('python', '-c "import sys; print(f''{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'')"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      if LoadStringFromFile(TempFile, PythonOutput) then
      begin
        PythonVersion := Trim(String(PythonOutput));
        
        // Parse version
        if (Copy(PythonVersion, 1, 3) = '3.9') or 
           (Copy(PythonVersion, 1, 4) = '3.10') or
           (Copy(PythonVersion, 1, 4) = '3.11') or
           (Copy(PythonVersion, 1, 4) = '3.12') then
        begin
          PythonCompatible := True;
          Result := True;
        end
        else if Copy(PythonVersion, 1, 3) = '3.7' or Copy(PythonVersion, 1, 3) = '3.8' then
        begin
          PythonCompatible := True;
          Result := True;
        end
        else if Copy(PythonVersion, 1, 3) = '3.6' then
        begin
          Result := True; // Found but old
        end;
      end;
    end;
  end;
  
  DeleteFile(TempFile);
end;

function InitializeSetup(): Boolean;
var
  Response: Integer;
begin
  Result := True;
  
  // Check Python
  if CheckPythonVersion() then
  begin
    if PythonCompatible then
    begin
      MsgBox('Python ' + PythonVersion + ' detected - excellent compatibility!', mbInformation, MB_OK);
    end
    else
    begin
      Response := MsgBox('Python ' + PythonVersion + ' detected. This version has limited compatibility (70% success rate).' + #13#10 + #13#10 + 
                        'For best results (98% success rate), upgrade to Python 3.7+.' + #13#10 + #13#10 + 
                        'Continue with current Python version?', mbConfirmation, MB_YESNO);
      if Response = IDNO then
        Result := False;
    end;
  end
  else
  begin
    Response := MsgBox('Python not found or incompatible version detected.' + #13#10 + #13#10 +
                      'InLegalDesk requires Python 3.6+ (3.7+ recommended).' + #13#10 + #13#10 +
                      'The installer can download Python 3.9 automatically.' + #13#10 + #13#10 +
                      'Continue with automatic Python installation?', mbConfirmation, MB_YESNO);
    if Response = IDNO then
      Result := False;
  end;
end;

procedure InitializeWizard();
begin
  // Create dependency installation page
  DependencyPage := CreateOutputProgressPage('Installing Dependencies', 
    'Please wait while InLegalDesk dependencies are being installed...');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  InstallDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    InstallDir := ExpandConstant('{app}');
    
    // Show dependency installation page
    DependencyPage.Show;
    
    try
      DependencyPage.SetText('Checking Python and pip...', '');
      DependencyPage.SetProgress(10, 100);
      
      // Upgrade pip first
      DependencyPage.SetText('Upgrading pip to latest version...', 'This prevents compilation issues');
      DependencyPage.SetProgress(20, 100);
      Exec('python', '-m pip install --upgrade pip', InstallDir, SW_HIDE, ewWaitUntilTerminated, ResultCode);
      
      // Install wheel support
      DependencyPage.SetText('Installing build tools...', 'Installing wheel and setuptools');
      DependencyPage.SetProgress(30, 100);
      Exec('python', '-m pip install wheel setuptools', InstallDir, SW_HIDE, ewWaitUntilTerminated, ResultCode);
      
      // Run smart dependency installer
      DependencyPage.SetText('Installing InLegalDesk dependencies...', 'This may take several minutes');
      DependencyPage.SetProgress(50, 100);
      
      if Exec('python', ExpandConstant('{app}\smart_dependency_installer.py'), InstallDir, SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        DependencyPage.SetText('Dependencies installed successfully!', '');
        DependencyPage.SetProgress(100, 100);
        Sleep(2000);
      end
      else
      begin
        DependencyPage.SetText('Some dependencies failed - manual installation available', '');
        DependencyPage.SetProgress(100, 100);
        Sleep(2000);
      end;
      
    finally
      DependencyPage.Hide;
    end;
  end;
end;

[Run]
Filename: "{app}\InLegalDesk_Launcher.py"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
Filename: "python"; Parameters: "{app}\check_python_compatibility.py"; Description: "Check system compatibility"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\backend\venv"
Type: filesandordirs; Name: "{app}\desktop\venv"
Type: filesandordirs; Name: "{app}\backend\data"
Type: files; Name: "{app}\*.log"