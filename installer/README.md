# InLegal Desktop Installer

This directory contains the build scripts and installer configuration for creating a Windows installer for the InLegal Desktop application.

## Prerequisites

### Required Software

1. **Python 3.9+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure Python is added to PATH during installation

2. **Inno Setup 6**
   - Download from [jrsoftware.org](https://jrsoftware.org/isinfo.php)
   - Install with default settings

3. **Git** (optional, for cloning the repository)
   - Download from [git-scm.com](https://git-scm.com/download/win)

### System Requirements

- Windows 10/11 (64-bit)
- 8GB RAM minimum (16GB recommended)
- 2GB free disk space
- Internet connection for downloading dependencies

## Building the Installer

### Quick Build

Run the PowerShell build script from the installer directory:

```powershell
cd installer
.\build_installer.ps1
```

### Build Options

```powershell
# Clean previous builds
.\build_installer.ps1 -Clean

# Skip PyInstaller build (if executable already exists)
.\build_installer.ps1 -SkipBuild

# Use specific Python path
.\build_installer.ps1 -PythonPath "C:\Python39\python.exe"

# Specify output directory
.\build_installer.ps1 -OutputDir "C:\MyOutput"
```

### Manual Build Steps

If you prefer to build manually:

1. **Create Virtual Environment**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```powershell
   pip install --upgrade pip
   pip install pyinstaller
   pip install -r ..\desktop\requirements.txt
   pip install -r ..\backend\requirements.txt
   ```

3. **Copy Server Files**
   ```powershell
   # Copy backend files to desktop/server directory
   # (This is handled automatically by the build script)
   ```

4. **Build Executable**
   ```powershell
   cd ..\desktop
   pyinstaller --noconfirm --onedir --name InLegalDesk main.py --add-data "server;server" --add-data ".env.sample;.env.sample"
   ```

5. **Create Installer**
   ```powershell
   cd ..\installer
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" InLegalDesk.iss
   ```

## Installer Features

### Installation Options

- **Installation Directory**: `C:\Program Files\InLegal Desktop`
- **Start Menu Shortcut**: Automatically created
- **Desktop Shortcut**: Optional (unchecked by default)
- **Quick Launch Shortcut**: Optional (Windows 7/8 only)

### Installed Components

- `InLegalDesk.exe` - Main application executable
- `server/` - Backend server files
- `.env.sample` - Environment configuration template
- `README.txt` - User documentation
- `LICENSE.txt` - License information

### Data Directory Structure

The installer creates the following data directories:

```
C:\Program Files\InLegal Desktop\
├── data\
│   ├── uploads\          # Uploaded documents
│   ├── downloads\        # Downloaded statutes
│   ├── chunks\          # Document chunks
│   └── embeddings\      # FAISS indexes
├── logs\                # Application logs
└── server\              # Backend server files
```

## Customization

### Icon Customization

1. Replace `icon.ico` with your custom icon
2. Ensure the icon is 256x256 pixels or larger
3. Rebuild the installer

### Silent Installation

The installer supports silent installation:

```cmd
InLegalDesk_Installer.exe /SILENT
```

Additional silent installation options:

- `/VERYSILENT` - No progress window
- `/NORESTART` - Don't restart if required
- `/DIR="C:\CustomPath"` - Custom installation directory

### Uninstallation

The installer creates an uninstaller that:

- Removes all application files
- Removes shortcuts
- Optionally removes user data (with confirmation)
- Removes registry entries

## Distribution

### File Size

The installer is typically 200-500 MB depending on included dependencies:

- Base application: ~50 MB
- PyTorch: ~200 MB
- Transformers: ~100 MB
- Other dependencies: ~50-100 MB

### Distribution Methods

1. **Direct Download**: Host the installer on your website
2. **GitHub Releases**: Upload to GitHub releases
3. **Package Managers**: Consider creating a Chocolatey package
4. **Enterprise**: Use Group Policy for enterprise deployment

### Digital Signing

For production distribution, consider code signing:

1. Obtain a code signing certificate
2. Sign the installer executable
3. Sign the main application executable

## Troubleshooting

### Common Issues

1. **Python Not Found**
   - Ensure Python 3.9+ is installed and in PATH
   - Use `-PythonPath` parameter to specify custom Python location

2. **Inno Setup Not Found**
   - Install Inno Setup 6 from the official website
   - Ensure it's installed in the default location

3. **Build Failures**
   - Check that all dependencies are installed
   - Ensure sufficient disk space (2GB+)
   - Try running with `-Clean` parameter

4. **Large Installer Size**
   - This is normal due to ML dependencies
   - Consider using `--onefile` for PyInstaller (slower startup)
   - Use `--exclude-module` to exclude unused modules

### Build Logs

Check the following for detailed error information:

- PowerShell console output
- PyInstaller logs in `desktop/build/`
- Inno Setup logs in `installer/output/`

### Support

For build issues:

1. Check the troubleshooting section above
2. Review build logs for specific errors
3. Ensure all prerequisites are installed
4. Try a clean build with `-Clean` parameter

## Development

### Modifying the Installer

Edit `InLegalDesk.iss` to modify:

- Installation options
- File associations
- Registry entries
- Custom installation steps

### Testing

Test the installer on:

- Clean Windows 10/11 systems
- Systems with/without Python
- Different user permission levels
- Various installation directories

### Version Management

Update the version in:

- `InLegalDesk.iss` - `#define MyAppVersion`
- `desktop/main.py` - Application version
- `backend/app.py` - API version