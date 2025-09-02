# InLegalDesk Windows Installer

This directory contains the Windows installer build system for InLegalDesk.

## Prerequisites

### Required Software

1. **Python 3.8+** - For building the application
2. **Inno Setup 6** - For creating the Windows installer
   - Download from: https://jrsoftware.org/isinfo.php
   - Install to default location

### Optional Software

- **Git** - For version control
- **Visual Studio Code** - For editing scripts

## Build Process

### Quick Build

Run the PowerShell build script:

```powershell
.\build_installer.ps1
```

### Build Options

```powershell
# Build with specific Python path
.\build_installer.ps1 -PythonPath "C:\Python39\python.exe"

# Build onefile executable (single .exe file)
.\build_installer.ps1 -BuildType "onefile"

# Build onedir executable (folder with dependencies)
.\build_installer.ps1 -BuildType "onedir"

# Skip executable build (only create installer)
.\build_installer.ps1 -SkipBuild

# Skip installer creation (only build executable)
.\build_installer.ps1 -SkipInstaller

# Clean previous builds before building
.\build_installer.ps1 -Clean
```

### Manual Build Steps

If you prefer to build manually:

1. **Create Virtual Environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**
   ```powershell
   pip install --upgrade pip
   pip install pyinstaller
   pip install -r ..\desktop\requirements.txt
   pip install -r ..\requirements.txt
   ```

3. **Build Executable**
   ```powershell
   # Onefile build
   pyinstaller --noconfirm --onefile --name InLegalDesk ..\desktop\main.py --add-data "..\desktop\server;server" --add-data "..\desktop\.env.sample;.env.sample"

   # Onedir build
   pyinstaller --noconfirm --onedir --name InLegalDesk ..\desktop\main.py --add-data "..\desktop\server;server" --add-data "..\desktop\.env.sample;.env.sample"
   ```

4. **Create Installer**
   ```powershell
   # Run Inno Setup compiler
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" InLegalDesk.iss
   ```

## Output Files

After successful build:

- **Executable**: `dist\InLegalDesk\InLegalDesk.exe` (onedir) or `dist\InLegalDesk.exe` (onefile)
- **Installer**: `installer\output\InLegalDesk_Installer.exe`

## Installer Features

The Windows installer includes:

- **Automatic Installation**: Installs to Program Files
- **Start Menu Shortcuts**: Creates shortcuts in Start Menu
- **Desktop Shortcut**: Optional desktop shortcut
- **Uninstaller**: Complete uninstallation support
- **File Associations**: Associates with .pdf files (optional)
- **System Integration**: Integrates with Windows

## Customization

### Icon

Replace `icon.ico` with your custom icon file (256x256 pixels recommended).

### Installer Script

Edit `InLegalDesk.iss` to customize:

- Application name and version
- Installation directory
- File associations
- Registry entries
- Custom installation steps

### Build Script

Edit `build_installer.ps1` to modify:

- Build parameters
- Dependencies
- Output locations
- Custom build steps

## Silent Installation

The installer supports silent installation:

```cmd
InLegalDesk_Installer.exe /SILENT
InLegalDesk_Installer.exe /VERYSILENT
InLegalDesk_Installer.exe /SILENT /NORESTART
```

### Silent Installation Parameters

- `/SILENT` - Silent installation with progress window
- `/VERYSILENT` - Silent installation without progress window
- `/NORESTART` - Don't restart after installation
- `/DIR="C:\CustomPath"` - Custom installation directory
- `/GROUP="CustomGroup"` - Custom Start Menu group
- `/NOICONS` - Don't create shortcuts
- `/DESKTOPICON` - Create desktop shortcut
- `/QUICKLAUNCHICON` - Create quick launch shortcut

## Troubleshooting

### Common Issues

1. **Python Not Found**
   - Ensure Python is in PATH or specify full path with `-PythonPath`

2. **Inno Setup Not Found**
   - Install Inno Setup 6 to default location
   - Or modify the script to point to your installation

3. **PyInstaller Fails**
   - Check that all dependencies are installed
   - Try building with `--onedir` instead of `--onefile`

4. **Installer Compilation Fails**
   - Check Inno Setup script syntax
   - Ensure all referenced files exist
   - Check file paths in the script

### Debug Mode

Enable debug output:

```powershell
$VerbosePreference = "Continue"
.\build_installer.ps1
```

### Manual Testing

Test the executable before creating installer:

```powershell
# Test onedir build
.\dist\InLegalDesk\InLegalDesk.exe

# Test onefile build
.\dist\InLegalDesk.exe
```

## Distribution

### File Sizes

Typical file sizes:

- **Onefile Executable**: ~200-300 MB
- **Onedir Executable**: ~150-200 MB (folder)
- **Installer**: ~200-300 MB

### Distribution Methods

1. **Direct Download**: Host installer on website
2. **Package Managers**: Create Chocolatey package
3. **Enterprise**: Use Group Policy for deployment
4. **Cloud**: Upload to cloud storage

### Digital Signing

For production distribution, consider code signing:

1. Obtain code signing certificate
2. Sign the executable: `signtool sign /f certificate.pfx InLegalDesk.exe`
3. Sign the installer: `signtool sign /f certificate.pfx InLegalDesk_Installer.exe`

## Security Considerations

- The installer requires administrator privileges
- Files are installed to Program Files (system directory)
- Uninstaller removes all application files
- No sensitive data is stored in the installer

## Support

For issues with the installer build process:

1. Check this README for common solutions
2. Review the build script output for errors
3. Test individual components (Python, PyInstaller, Inno Setup)
4. Create an issue in the project repository