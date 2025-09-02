#!/usr/bin/env python3
"""
Check InLegalDesk release status
"""
import requests
import json
from datetime import datetime

def check_build_status():
    """Check GitHub Actions and release status"""
    print("🔍 Checking InLegalDesk Release Status")
    print("=" * 40)
    
    repo = "ravidatanerd/LEGAL_BERT_IN"
    
    try:
        # Check latest release
        print("\n📦 Checking Releases...")
        releases_url = f"https://api.github.com/repos/{repo}/releases"
        response = requests.get(releases_url, timeout=10)
        
        if response.status_code == 200:
            releases = response.json()
            if releases:
                latest = releases[0]
                print(f"✅ Latest Release: {latest['tag_name']}")
                print(f"   Published: {latest['published_at']}")
                print(f"   Assets: {len(latest['assets'])} files")
                
                if latest['assets']:
                    print("   📥 Downloads:")
                    for asset in latest['assets']:
                        size_mb = asset['size'] / (1024 * 1024)
                        print(f"      • {asset['name']} ({size_mb:.1f} MB)")
                        print(f"        Download: {asset['browser_download_url']}")
                else:
                    print("   ⚠️  No download files yet (build may be in progress)")
            else:
                print("⚠️  No releases found yet")
        else:
            print(f"❌ Could not fetch releases: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error checking releases: {e}")
    
    try:
        # Check workflow runs
        print("\n🔄 Checking GitHub Actions...")
        actions_url = f"https://api.github.com/repos/{repo}/actions/runs"
        response = requests.get(actions_url, timeout=10)
        
        if response.status_code == 200:
            runs = response.json()
            if runs['workflow_runs']:
                latest_run = runs['workflow_runs'][0]
                status = latest_run['status']
                conclusion = latest_run['conclusion']
                
                print(f"✅ Latest Build: {latest_run['name']}")
                print(f"   Status: {status}")
                print(f"   Conclusion: {conclusion}")
                print(f"   Started: {latest_run['created_at']}")
                
                if status == "completed":
                    if conclusion == "success":
                        print("   🎉 BUILD SUCCESSFUL!")
                    elif conclusion == "failure":
                        print("   ❌ Build failed - check logs")
                    else:
                        print(f"   ⚠️  Build completed with: {conclusion}")
                elif status == "in_progress":
                    print("   🟡 Build in progress...")
                else:
                    print(f"   ❓ Status: {status}")
                    
                print(f"   View: https://github.com/{repo}/actions/runs/{latest_run['id']}")
            else:
                print("⚠️  No workflow runs found")
        else:
            print(f"❌ Could not fetch actions: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking actions: {e}")
    
    # Always provide immediate access info
    print(f"\n🚀 IMMEDIATE ACCESS (Available Now):")
    print(f"1. Repository: https://github.com/{repo}")
    print(f"2. Source Download: Click 'Code' → 'Download ZIP'")
    print(f"3. Setup Guide: Follow IMMEDIATE_DOWNLOAD.md")
    print(f"4. Full Platform: Hybrid BERT+GPT AI ready to use!")
    
    print(f"\n📊 Repository Stats:")
    try:
        repo_url = f"https://api.github.com/repos/{repo}"
        response = requests.get(repo_url, timeout=10)
        if response.status_code == 200:
            repo_data = response.json()
            print(f"   ⭐ Stars: {repo_data['stargazers_count']}")
            print(f"   🍴 Forks: {repo_data['forks_count']}")
            print(f"   👀 Watchers: {repo_data['watchers_count']}")
            print(f"   📊 Size: {repo_data['size']} KB")
        else:
            print(f"   ❌ Could not fetch repo stats")
    except Exception as e:
        print(f"   ❌ Error fetching stats: {e}")

if __name__ == "__main__":
    check_build_status()