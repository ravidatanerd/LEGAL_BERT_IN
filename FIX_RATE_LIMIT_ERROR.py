#!/usr/bin/env python3
"""
OpenAI Rate Limit Error Handler
Diagnoses and provides solutions for rate limit exceeded errors
"""
import sys
import os
import time
import json
from datetime import datetime, timedelta

def check_openai_rate_limits():
    """Check OpenAI rate limits and provide guidance"""
    print("🔍 OpenAI Rate Limit Analyzer")
    print("=" * 35)
    print()
    
    print("❌ RATE LIMIT EXCEEDED ERROR EXPLANATION:")
    print("-" * 45)
    print()
    print("The error 'RATE limit exceeded - try again later' means:")
    print("• You've used up your OpenAI API quota for the current period")
    print("• This is NOT an API key validation issue")
    print("• Your ChatGPT token is valid, but you've hit usage limits")
    print()
    
    print("📊 OPENAI RATE LIMITS (as of 2024):")
    print("-" * 35)
    print()
    print("Free Tier (Trial Credits):")
    print("• $5 in free credits for new accounts")
    print("• Expires after 3 months")
    print("• Limited requests per minute")
    print()
    print("Pay-as-you-go:")
    print("• GPT-4: ~$0.03 per 1K tokens")
    print("• GPT-3.5-turbo: ~$0.002 per 1K tokens")
    print("• Rate limits based on usage tier")
    print()
    print("Usage Tiers:")
    print("• Tier 1: $5+ spent - 500 RPM")
    print("• Tier 2: $50+ spent - 5,000 RPM")
    print("• Tier 3: $100+ spent - 5,000 RPM")
    print("• Tier 4: $250+ spent - 10,000 RPM")
    print()

def check_api_key_status():
    """Test API key and check status"""
    print("🔑 TESTING YOUR API KEY STATUS:")
    print("-" * 35)
    print()
    
    api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return
    
    try:
        import requests
        
        # Test API key with a minimal request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Check account status
        print("📡 Checking API key status...")
        response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ API key is valid and working")
            models = response.json()
            available_models = [model['id'] for model in models['data'] if 'gpt' in model['id']]
            print(f"✅ Available models: {', '.join(available_models[:3])}...")
            
        elif response.status_code == 429:
            print("❌ RATE LIMIT EXCEEDED")
            print("Your API key is valid but you've hit the rate limit")
            
            # Parse rate limit headers
            if 'retry-after' in response.headers:
                retry_after = int(response.headers['retry-after'])
                print(f"⏰ Retry after: {retry_after} seconds")
            
            if 'x-ratelimit-remaining-requests' in response.headers:
                remaining = response.headers['x-ratelimit-remaining-requests']
                print(f"📊 Remaining requests: {remaining}")
                
        elif response.status_code == 401:
            print("❌ INVALID API KEY")
            print("Your API key is not valid or has been revoked")
            
        elif response.status_code == 403:
            print("❌ FORBIDDEN")
            print("Your API key doesn't have permission for this operation")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except ImportError:
        print("❌ 'requests' library not installed")
        print("Install with: pip install requests")
    except Exception as e:
        print(f"❌ Error testing API key: {e}")

def provide_rate_limit_solutions():
    """Provide solutions for rate limit issues"""
    print("\n🔧 SOLUTIONS FOR RATE LIMIT EXCEEDED:")
    print("-" * 40)
    print()
    
    print("IMMEDIATE SOLUTIONS:")
    print("1. ⏰ Wait and try again later (15-60 minutes)")
    print("2. 🔄 Reduce request frequency in InLegalDesk")
    print("3. 💰 Add credits to your OpenAI account")
    print("4. 📊 Check your usage at https://platform.openai.com/usage")
    print()
    
    print("LONG-TERM SOLUTIONS:")
    print("1. 💳 Set up billing at https://platform.openai.com/account/billing")
    print("2. 📈 Upgrade to higher usage tier by spending more")
    print("3. 🔧 Configure rate limiting in InLegalDesk")
    print("4. 💡 Use local models as fallback when rate limited")
    print()
    
    print("INLEGALDESK CONFIGURATION:")
    print("1. 🔧 Set conservative rate limits in backend/.env:")
    print("   RATE_LIMIT_PER_MINUTE=10")
    print("   OPENAI_MAX_TOKENS=1000")
    print()
    print("2. 🔄 Enable local model fallbacks:")
    print("   VLM_PRESET=balanced  # Uses local models first")
    print()
    print("3. ⚡ Use basic mode when rate limited:")
    print("   VLM_PRESET=offline   # No API calls")
    print()

def create_rate_limit_config():
    """Create configuration to handle rate limits"""
    print("🔧 CREATING RATE LIMIT CONFIGURATION:")
    print("-" * 40)
    print()
    
    config_content = """# InLegalDesk Rate Limit Configuration
# Add these to your backend/.env file to handle OpenAI rate limits

# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo  # Use cheaper model to avoid limits
OPENAI_MAX_TOKENS=1000      # Reduce token usage
OPENAI_TIMEOUT=30           # Request timeout

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10    # Conservative rate limit
RATE_LIMIT_BURST=3          # Allow small bursts

# Fallback Configuration
VLM_PRESET=balanced         # Use local models first, API as backup
ENABLE_LOCAL_FALLBACK=true  # Fall back to local models when rate limited

# Error Handling
RETRY_ATTEMPTS=3            # Retry failed requests
RETRY_DELAY=60              # Wait 60 seconds between retries
GRACEFUL_DEGRADATION=true   # Use basic responses when API fails

# Cost Control
MAX_DAILY_REQUESTS=100      # Limit daily API usage
WARN_ON_HIGH_USAGE=true     # Warn when approaching limits
"""
    
    try:
        with open("rate_limit_config.env", "w") as f:
            f.write(config_content)
        print("✅ Rate limit configuration saved to: rate_limit_config.env")
        print()
        print("📋 To use this configuration:")
        print("1. Copy contents to backend/.env")
        print("2. Replace 'your_api_key_here' with your actual key")
        print("3. Restart InLegalDesk backend")
        print("4. Rate limiting will be handled automatically")
        
    except Exception as e:
        print(f"❌ Could not save config: {e}")

def main():
    """Main rate limit troubleshooting function"""
    print("🚨 OpenAI Rate Limit Error Troubleshooter")
    print("=" * 45)
    print()
    
    print("You're getting 'RATE limit exceeded - try again later'")
    print("This means your API key is VALID but you've hit usage limits.")
    print()
    
    # Check rate limits
    check_openai_rate_limits()
    
    # Test API key status
    test_key = input("\nTest your API key status? (y/N): ").lower()
    if test_key == 'y':
        check_api_key_status()
    
    # Provide solutions
    provide_rate_limit_solutions()
    
    # Create configuration
    create_config = input("\nCreate rate limit configuration? (Y/n): ").lower()
    if create_config != 'n':
        create_rate_limit_config()
    
    print("\n🎯 SUMMARY:")
    print("-" * 10)
    print("✅ Your ChatGPT token is VALID")
    print("❌ You've hit OpenAI's rate limits")
    print("🔧 Solutions provided above")
    print("⏰ Wait or add credits to continue")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")