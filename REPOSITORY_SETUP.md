name: Secure Private Release Build

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Release version (e.g., v1.0.0)'
        required: true
        default: 'v1.0.0'

env:
  PYTHON_VERSION: '3.11'
  
jobs:
  security-scan:
    runs-on: ubuntu-latest
    name: Security Scan
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Run security scan
      run: |
        echo "🔍 Scanning for secrets and vulnerabilities..."
        
        # Check for accidentally committed secrets
        if grep -r "sk-[a-zA-Z0-9]\{20,\}" . --exclude-dir=.git; then
          echo "❌ SECURITY ALERT: API keys found in repository!"
          exit 1
        fi
        
        # Check for hardcoded passwords
        if grep -r "password.*=" . --include="*.py" | grep -v "placeholder\|example\|sample"; then
          echo "❌ SECURITY ALERT: Hardcoded passwords found!"
          exit 1
        fi
        
        echo "✅ Security scan passed"

  build-windows-installer:
    needs: security-scan
    runs-on: windows-latest
    name: Build Windows Installer
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        
    - name: Cache Python dependencies
      uses: actions/cache@v3
      with:
        path: ~\AppData\Local\pip\Cache
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        
    - name: Install Inno Setup
      run: |
        Write-Host "Installing Inno Setup..."
        Invoke-WebRequest -Uri "https://jrsoftware.org/download.php/is.exe" -OutFile "innosetup.exe"
        Start-Process -FilePath "innosetup.exe" -ArgumentList "/SILENT" -Wait
        Write-Host "✅ Inno Setup installed"
        
    - name: Prepare build environment
      run: |
        Write-Host "🔧 Preparing build environment..."
        
        # Create build directory
        New-Item -ItemType Directory -Force -Path "build"
        
        # Copy source files
        Copy-Item -Recurse -Force "backend" "build/"
        Copy-Item -Recurse -Force "desktop" "build/"
        Copy-Item -Recurse -Force "installer" "build/"
        
        Write-Host "✅ Build environment prepared"
        
    - name: Build desktop application
      run: |
        Write-Host "🏗️ Building desktop application..."
        
        cd build/desktop
        
        # Create virtual environment
        python -m venv venv
        venv\Scripts\activate
        
        # Upgrade pip
        python -m pip install --upgrade pip
        
        # Install requirements
        pip install -r requirements.txt
        pip install pyinstaller
        
        # Copy backend to server directory
        if (Test-Path "server") { Remove-Item -Recurse -Force "server" }
        Copy-Item -Recurse -Force "..\backend" "server"
        
        # Build executable
        pyinstaller --noconfirm --onedir --name InLegalDesk `
          --add-data "server;server" `
          --add-data ".env.sample;.env.sample" `
          --icon "..\installer\assets\icon.ico" `
          --distpath "..\installer\dist" `
          --workpath "..\installer\build" `
          main.py
          
        Write-Host "✅ Desktop application built"
        
    - name: Build installer
      run: |
        Write-Host "📦 Building Windows installer..."
        
        cd build/installer
        
        # Update ISS script with correct paths
        $issContent = Get-Content "InLegalDesk.iss" -Raw
        $issContent = $issContent -replace "#define BuildType .*", "#define BuildType `"onedir`""
        $issContent = $issContent -replace "#define DistDir .*", "#define DistDir `"dist`""
        Set-Content "InLegalDesk.iss" $issContent
        
        # Compile installer
        & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "InLegalDesk.iss"
        
        # Verify installer was created
        if (Test-Path "output\InLegalDesk_Installer.exe") {
          $size = (Get-Item "output\InLegalDesk_Installer.exe").Length / 1MB
          Write-Host "✅ Installer created successfully ($([math]::Round($size, 1)) MB)"
        } else {
          Write-Host "❌ Installer creation failed"
          exit 1
        }
        
    - name: Generate checksums
      run: |
        Write-Host "🔐 Generating security checksums..."
        
        cd build/installer/output
        
        # Generate SHA256 checksum
        $hash = Get-FileHash "InLegalDesk_Installer.exe" -Algorithm SHA256
        $hash.Hash | Out-File "InLegalDesk_Installer.exe.sha256"
        
        # Generate MD5 checksum
        $md5 = Get-FileHash "InLegalDesk_Installer.exe" -Algorithm MD5
        $md5.Hash | Out-File "InLegalDesk_Installer.exe.md5"
        
        Write-Host "✅ Checksums generated"
        
    - name: Upload installer artifact
      uses: actions/upload-artifact@v3
      with:
        name: InLegalDesk-Installer-${{ github.ref_name || github.event.inputs.version }}
        path: |
          build/installer/output/InLegalDesk_Installer.exe
          build/installer/output/*.sha256
          build/installer/output/*.md5
        retention-days: 90
        
    - name: Create private release
      if: startsWith(github.ref, 'refs/tags/') || github.event_name == 'workflow_dispatch'
      uses: softprops/action-gh-release@v1
      with:
        tag_name: ${{ github.ref_name || github.event.inputs.version }}
        name: InLegalDesk ${{ github.ref_name || github.event.inputs.version }} - Private Release
        body: |
          # 🤖 InLegalDesk Private Release ${{ github.ref_name || github.event.inputs.version }}
          
          ## 🔒 Private Distribution
          This is a private release for authorized users only.
          
          ## 📥 Download (Authorized Users Only)
          - **Windows Installer**: InLegalDesk_Installer.exe
          - **SHA256 Checksum**: InLegalDesk_Installer.exe.sha256
          - **MD5 Checksum**: InLegalDesk_Installer.exe.md5
          
          ## 🚀 Installation Instructions
          1. Download installer (requires repository access)
          2. Verify checksum for security
          3. Run as Administrator
          4. Configure API credentials after installation
          
          ## ✨ Features in This Release
          - 🤖 Hybrid BERT+GPT AI architecture
          - 🧠 InLegalBERT + T5 + XLNet integration
          - 🔒 Enhanced security with AES-256 encryption
          - ⚖️ Advanced Indian legal research capabilities
          - 💬 ChatGPT-style interface with hybrid analysis
          
          ## 🔐 Security Verification
          ```
          # Verify installer integrity
          certutil -hashfile InLegalDesk_Installer.exe SHA256
          # Compare with provided SHA256 checksum
          ```
          
          ## ⚠️ Important Notes
          - Private repository access required
          - OpenAI API key needed for full features
          - Windows 10/11 (64-bit) required
          - ~2GB disk space needed for full installation
        files: |
          build/installer/output/InLegalDesk_Installer.exe
          build/installer/output/*.sha256
          build/installer/output/*.md5
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Notify completion
      run: |
        Write-Host "🎉 Private release build completed successfully!"
        Write-Host "📦 Installer available in GitHub Releases (private)"
        Write-Host "🔒 Only repository collaborators can access the download"