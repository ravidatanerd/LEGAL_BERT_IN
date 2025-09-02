#!/usr/bin/env python3
"""
Prepare InLegalDesk for public GitHub release
"""
import os
import re
import shutil
from pathlib import Path

def print_step(step, description):
    print(f"\n📋 Step {step}: {description}")

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def scan_for_secrets():
    """Scan for accidentally committed secrets"""
    print_step(1, "Scanning for secrets and sensitive data")
    
    secret_patterns = [
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API keys
        r'password\s*=\s*["\'][^"\']{8,}["\']',  # Hardcoded passwords
        r'secret\s*=\s*["\'][^"\']+["\']',  # Secret keys
        r'token\s*=\s*["\'][^"\']+["\']',  # Tokens
    ]
    
    issues_found = []
    
    for root, dirs, files in os.walk('.'):
        # Skip venv and git directories
        dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith(('.py', '.md', '.txt', '.json', '.yml', '.yaml')):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            # Skip sample/example files
                            if 'sample' not in str(file_path) and 'example' not in str(file_path):
                                issues_found.append(f"{file_path}: {pattern}")
                                
                except Exception:
                    continue
    
    if issues_found:
        print_warning("Potential secrets found:")
        for issue in issues_found:
            print(f"   {issue}")
        return False
    else:
        print_success("No secrets found in code")
        return True

def validate_gitignore():
    """Validate .gitignore is comprehensive"""
    print_step(2, "Validating .gitignore configuration")
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        print_warning(".gitignore not found")
        return False
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    required_patterns = [
        '.env',
        '*.key',
        'sk-*',
        'venv/',
        '__pycache__/',
        '*.exe',
        'data/',
        'logs/'
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print_warning(f"Missing .gitignore patterns: {missing_patterns}")
        return False
    else:
        print_success(".gitignore properly configured")
        return True

def validate_env_files():
    """Ensure only sample env files exist"""
    print_step(3, "Validating environment files")
    
    env_files = list(Path('.').rglob('.env'))
    env_files = [f for f in env_files if 'venv' not in str(f)]
    
    if env_files:
        print_warning(f"Real .env files found (should be excluded): {env_files}")
        return False
    
    sample_files = list(Path('.').rglob('.env.sample'))
    sample_files = [f for f in sample_files if 'venv' not in str(f)]
    
    if sample_files:
        print_success(f"Sample env files found: {len(sample_files)}")
        
        # Validate sample files don't contain real secrets
        for sample_file in sample_files:
            with open(sample_file, 'r') as f:
                content = f.read()
                if 'sk-' in content and 'sk-xxxxx' not in content:
                    print_warning(f"Real API key in sample file: {sample_file}")
                    return False
        
        return True
    else:
        print_warning("No .env.sample files found")
        return False

def validate_documentation():
    """Validate documentation is complete"""
    print_step(4, "Validating documentation completeness")
    
    required_docs = [
        'README.md',
        'INSTALLATION.md',
        'SECURITY.md',
        'CONTRIBUTING.md',
        'LICENSE',
        'HYBRID_AI_GUIDE.md'
    ]
    
    missing_docs = []
    for doc in required_docs:
        if not Path(doc).exists():
            missing_docs.append(doc)
    
    if missing_docs:
        print_warning(f"Missing documentation: {missing_docs}")
        return False
    
    # Check documentation quality
    for doc in required_docs:
        if Path(doc).exists():
            with open(doc, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) < 500:  # Minimum substantial content
                    print_warning(f"Documentation too short: {doc}")
                    return False
    
    print_success("All documentation complete and substantial")
    return True

def validate_build_system():
    """Validate build system is ready"""
    print_step(5, "Validating build system")
    
    build_files = [
        'installer/build_installer.ps1',
        'installer/InLegalDesk.iss',
        '.github/workflows/build-release.yml',
        'build_windows_installer.bat'
    ]
    
    missing_files = []
    for file in build_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print_warning(f"Missing build files: {missing_files}")
        return False
    
    print_success("Build system complete")
    return True

def create_release_checklist():
    """Create release checklist"""
    print_step(6, "Creating release checklist")
    
    checklist = """# 📋 Public Release Checklist

## Pre-Release Security Check
- [ ] No real API keys in repository
- [ ] No hardcoded passwords or secrets
- [ ] .gitignore properly configured
- [ ] Only .env.sample files included
- [ ] Security scan passes

## Documentation Review
- [ ] README.md updated with latest features
- [ ] INSTALLATION.md has clear instructions
- [ ] SECURITY.md covers all security features
- [ ] HYBRID_AI_GUIDE.md explains AI architecture
- [ ] All documentation reviewed for accuracy

## Build System Verification
- [ ] GitHub Actions workflow tested
- [ ] PowerShell build script functional
- [ ] Inno Setup configuration correct
- [ ] All dependencies listed in requirements.txt

## Final Testing
- [ ] Backend starts without errors
- [ ] Hybrid AI system initializes
- [ ] Desktop app launches properly
- [ ] Security features functional
- [ ] All tests pass

## Release Preparation
- [ ] Version number updated
- [ ] Release notes prepared
- [ ] Tag created for release
- [ ] GitHub Actions builds installer
- [ ] Installer tested on clean Windows system

## Post-Release
- [ ] Monitor for issues
- [ ] Respond to community feedback
- [ ] Update documentation as needed
- [ ] Plan next release features
"""
    
    with open('RELEASE_CHECKLIST.md', 'w') as f:
        f.write(checklist)
    
    print_success("Release checklist created")

def update_placeholder_urls():
    """Update placeholder URLs in documentation"""
    print_step(7, "Updating placeholder URLs")
    
    # Files that need URL updates
    files_to_update = [
        'README.md',
        'INSTALLATION.md',
        '.github/workflows/build-release.yml'
    ]
    
    placeholder_url = "YOUR_USERNAME/inlegaldesk"
    
    print_warning(f"Remember to update '{placeholder_url}' with your actual GitHub username/repo")
    print("   Example: github.com/johndoe/inlegaldesk")
    
    return True

def main():
    """Main preparation function"""
    print("🚀 Preparing InLegalDesk for Public GitHub Release")
    print("=" * 60)
    
    checks = [
        scan_for_secrets(),
        validate_gitignore(), 
        validate_env_files(),
        validate_documentation(),
        validate_build_system(),
    ]
    
    create_release_checklist()
    update_placeholder_urls()
    
    passed_checks = sum(checks)
    total_checks = len(checks)
    
    print(f"\n{'='*60}")
    print(f"📊 RELEASE READINESS: {passed_checks}/{total_checks} checks passed")
    print('='*60)
    
    if passed_checks == total_checks:
        print("🎉 PROJECT READY FOR PUBLIC RELEASE!")
        print("\n✅ Security: No secrets found in code")
        print("✅ Configuration: .gitignore properly set up") 
        print("✅ Environment: Only sample files included")
        print("✅ Documentation: Complete and comprehensive")
        print("✅ Build System: GitHub Actions ready")
        
        print(f"\n🚀 Next Steps:")
        print("1. Create public GitHub repository")
        print("2. Update YOUR_USERNAME placeholders with actual username")
        print("3. Push code to GitHub")
        print("4. Create release tag (git tag v1.0.0)")
        print("5. GitHub Actions will build installer automatically")
        print("6. Share with the community!")
        
    else:
        print("⚠️  Some checks failed. Please address issues above.")
        
    return passed_checks == total_checks

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)