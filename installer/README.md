# InLegalDesk Windows Installer

This directory contains the build scripts and assets for creating a Windows installer for InLegalDesk.

## Prerequisites

### Required Software

1. **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
2. **Inno Setup 6+** - Download from [jrsoftware.org](https://jrsoftware.org/isinfo.php)
3. **PowerShell 5.0+** - Usually pre-installed on Windows 10+

### Optional Dependencies

- **Git** - For cloning the repository
- **Visual Studio Build Tools** - For compiling some Python packages

## Building the Installer

### Quick Build

Run the PowerShell build script from this directory:

```powershell
.\build_installer.ps1
```

### Advanced Build Options

```powershell
# Build onefile executable (single .exe)
.\build_installer.ps1 -BuildType onefile

# Build onedir executable (folder with dependencies)
.\build_installer.ps1 -BuildType onedir

# Specify custom Python path
.\build_installer.ps1 -PythonPath "C:\Python39\python.exe"

# Specify custom Inno Setup path
.\build_installer.ps1 -InnoSetupPath "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

### Manual Build Steps

If the PowerShell script doesn't work, you can build manually:

1. **Copy backend to desktop**:
   ```cmd
   xcopy /E /I ..\backend desktop\server
   ```

2. **Create virtual environment**:
   ```cmd
   python -m venv build\venv
   build\venv\Scripts\activate
   ```

3. **Install requirements**:
   ```cmd
   pip install -r ..\desktop\requirements.txt
   pip install pyinstaller
   ```

4. **Build executable**:
   ```cmd
   cd ..\desktop
   pyinstaller --noconfirm --onedir --name InLegalDesk ^
     --add-data "server;server" ^
     --add-data ".env.sample;.env.sample" ^
     --icon "..\installer\assets\icon.ico" ^
     main.py
   ```

5. **Build installer**:
   ```cmd
   cd ..\installer
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" InLegalDesk.iss
   ```

## Build Outputs

- **Executable**: `dist\InLegalDesk\InLegalDesk.exe` (onedir) or `dist\InLegalDesk.exe` (onefile)
- **Installer**: `output\InLegalDesk_Installer.exe`

## Installer Features

### Installation Options

- **Default Installation**: Installs to `C:\Program Files\InLegalDesk\`
- **Custom Directory**: User can choose installation directory
- **Desktop Shortcut**: Optional desktop icon
- **Start Menu**: Creates Start Menu entries
- **File Association**: Optional PDF file association

### Silent Installation

For automated deployment:

```cmd
# Silent install to default location
InLegalDesk_Installer.exe /SILENT

# Silent install to custom location
InLegalDesk_Installer.exe /SILENT /DIR="C:\MyApps\InLegalDesk"

# Very silent (no UI at all)
InLegalDesk_Installer.exe /VERYSILENT /DIR="C:\MyApps\InLegalDesk"

# Silent with desktop icon
InLegalDesk_Installer.exe /SILENT /TASKS="desktopicon"
```

### Uninstallation

- **Control Panel**: Standard Windows uninstall
- **Start Menu**: "Uninstall InLegalDesk" shortcut
- **Silent Uninstall**: 
  ```cmd
  "C:\Program Files\InLegalDesk\unins000.exe" /SILENT
  ```

## Customization

### Icon

Replace `assets\icon.ico` with your custom icon. Requirements:
- Format: ICO file
- Sizes: 16x16, 32x32, 48x48, 256x256
- Color depth: 32-bit with alpha channel

### Branding

Edit `InLegalDesk.iss` to customize:
- Company name (`AppPublisher`)
- Website URL (`AppURL`)
- Application description
- License file path
- Welcome/finish page text

### Build Configuration

Edit `build_installer.ps1` to modify:
- Default Python path
- Default Inno Setup path
- Build output directories
- Additional PyInstaller options

## Troubleshooting

### Common Issues

1. **Python not found**
   - Ensure Python is in PATH
   - Use `-PythonPath` parameter to specify location

2. **Inno Setup not found**
   - Install Inno Setup 6
   - Use `-InnoSetupPath` parameter

3. **PyInstaller fails**
   - Check all dependencies are installed
   - Try building in a clean virtual environment
   - Check for antivirus interference

4. **Large installer size**
   - Use `onefile` build type for smaller distribution
   - Consider excluding unnecessary dependencies

### Build Logs

Check these files for detailed error information:
- `build\build.log` - PyInstaller build log
- `output\InLegalDesk_Installer.log` - Inno Setup compilation log

### Performance Tips

- **Onedir vs Onefile**: Onedir starts faster but creates more files
- **Antivirus**: Add build directory to antivirus exclusions
- **SSD**: Build on SSD for faster compilation

## Distribution

### Signing (Optional)

For production distribution, sign the executable and installer:

```cmd
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com InLegalDesk.exe
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com InLegalDesk_Installer.exe
```

### Testing

Test the installer on clean Windows systems:
- Windows 10 (minimum supported version)
- Windows 11
- Without Python pre-installed
- Different user privilege levels

### Deployment

The installer can be distributed via:
- Direct download from website
- Windows Package Manager (winget)
- Chocolatey package manager
- Enterprise deployment tools (SCCM, etc.)

## Support

For build issues or questions:
1. Check the troubleshooting section above
2. Review build logs in the `build\` directory
3. Ensure all prerequisites are properly installed
4. Try building on a clean Windows system