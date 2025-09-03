#!/usr/bin/env python3
"""
API Key Fixer for ChatGPT Tokens
Automatically fixes common API key issues and validates format
"""
import re
import sys

def clean_api_key(raw_key: str) -> str:
    """Clean common API key copy-paste issues"""
    
    # Remove whitespace
    cleaned = raw_key.strip()
    
    # Remove surrounding quotes
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1]
    
    # Remove any newlines or tabs
    cleaned = cleaned.replace('\n', '').replace('\r', '').replace('\t', '')
    
    # Remove any accidentally copied text
    if 'API Key:' in cleaned:
        cleaned = cleaned.split('API Key:')[-1].strip()
    
    if 'Bearer ' in cleaned:
        cleaned = cleaned.replace('Bearer ', '')
    
    return cleaned

def validate_and_fix_api_key(api_key: str) -> dict:
    """Validate and attempt to fix API key issues"""
    
    result = {
        "original_key": api_key,
        "cleaned_key": "",
        "is_valid": False,
        "issues_found": [],
        "fixes_applied": [],
        "final_status": ""
    }
    
    # Step 1: Clean the key
    cleaned_key = clean_api_key(api_key)
    result["cleaned_key"] = cleaned_key
    
    if cleaned_key != api_key:
        result["fixes_applied"].append("Removed whitespace and formatting")
    
    # Step 2: Analyze the cleaned key
    if not cleaned_key:
        result["issues_found"].append("API key is empty after cleaning")
        result["final_status"] = "INVALID - Empty key"
        return result
    
    # Check prefix
    valid_prefixes = ['sk-', 'sk-proj-', 'sk-svcacct-']
    has_valid_prefix = any(cleaned_key.startswith(prefix) for prefix in valid_prefixes)
    
    if not has_valid_prefix:
        result["issues_found"].append(f"Invalid prefix. Must start with: {', '.join(valid_prefixes)}")
        result["final_status"] = "INVALID - Wrong prefix"
        return result
    
    # Determine key type
    if cleaned_key.startswith('sk-proj-'):
        key_type = "Project API Key"
        expected_length_min = 40
    elif cleaned_key.startswith('sk-svcacct-'):
        key_type = "Service Account Key"
        expected_length_min = 40
    else:
        key_type = "Standard API Key"
        expected_length_min = 20
    
    result["key_type"] = key_type
    
    # Check length
    if len(cleaned_key) < expected_length_min:
        result["issues_found"].append(f"Key too short for {key_type} (minimum {expected_length_min} chars)")
        result["final_status"] = "INVALID - Too short"
        return result
    
    if len(cleaned_key) > 300:
        result["issues_found"].append("Key too long (maximum 300 characters)")
        result["final_status"] = "INVALID - Too long"
        return result
    
    # Check character set
    # Modern OpenAI keys can contain: letters, numbers, hyphens, underscores
    allowed_pattern = r'^sk-(?:proj-|svcacct-)?[a-zA-Z0-9_-]+$'
    
    if not re.match(allowed_pattern, cleaned_key):
        # Find invalid characters
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        
        # Skip the prefix when checking characters
        if cleaned_key.startswith('sk-proj-'):
            key_body = cleaned_key[8:]  # Skip 'sk-proj-'
        elif cleaned_key.startswith('sk-svcacct-'):
            key_body = cleaned_key[11:]  # Skip 'sk-svcacct-'
        else:
            key_body = cleaned_key[3:]  # Skip 'sk-'
        
        key_chars = set(key_body)
        invalid_chars = key_chars - allowed_chars
        
        if invalid_chars:
            result["issues_found"].append(f"Invalid characters found: {', '.join(sorted(invalid_chars))}")
            result["invalid_characters"] = list(invalid_chars)
            result["final_status"] = "INVALID - Invalid characters"
            return result
    
    # If we get here, the key is valid
    result["is_valid"] = True
    result["final_status"] = "VALID"
    
    # Create masked version
    if len(cleaned_key) > 15:
        if cleaned_key.startswith('sk-proj-'):
            result["masked_key"] = "sk-proj-..." + cleaned_key[-6:]
        elif cleaned_key.startswith('sk-svcacct-'):
            result["masked_key"] = "sk-svcacct-..." + cleaned_key[-6:]
        else:
            result["masked_key"] = "sk-..." + cleaned_key[-6:]
    else:
        result["masked_key"] = "sk-****"
    
    return result

def main():
    """Main API key fixing function"""
    print("🔑 ChatGPT API Key Fixer & Validator")
    print("=" * 40)
    print()
    print("This tool fixes common API key issues and validates")
    print("compatibility with the latest ChatGPT token formats.")
    print()
    
    # Get API key
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print("Using API key from command line argument...")
    else:
        print("Enter your ChatGPT/OpenAI API key:")
        print("(It will be masked in the output for security)")
        api_key = input("API Key: ")
    
    if not api_key.strip():
        print("❌ No API key provided")
        return
    
    print("\n🔧 ANALYZING AND FIXING API KEY...")
    print("-" * 35)
    
    # Validate and fix
    result = validate_and_fix_api_key(api_key)
    
    # Show results
    print(f"📊 Key Type: {result.get('key_type', 'Unknown')}")
    print(f"📏 Length: {len(result['cleaned_key'])} characters")
    print(f"🎭 Masked: {result['masked_key']}")
    print()
    
    if result["fixes_applied"]:
        print("🔧 FIXES APPLIED:")
        for fix in result["fixes_applied"]:
            print(f"   ✅ {fix}")
        print()
    
    if result["issues_found"]:
        print("❌ ISSUES FOUND:")
        for issue in result["issues_found"]:
            print(f"   • {issue}")
        print()
        
        if "invalid_characters" in result:
            print("🔍 INVALID CHARACTERS DETAILS:")
            for char in result["invalid_characters"]:
                print(f"   • '{char}' (Unicode: U+{ord(char):04X})")
            print()
        
        print("🔧 SOLUTIONS:")
        print("1. Copy the API key again from OpenAI dashboard")
        print("2. Make sure no extra characters are copied")
        print("3. Avoid copying surrounding quotes or spaces")
        print("4. Check that the key is complete")
        print()
        
    else:
        print("✅ API KEY IS VALID!")
        print("Your ChatGPT API key format is correct and should work")
        print("with InLegalDesk.")
        print()
        
        # Show how to use it
        print("🔧 HOW TO USE IN INLEGALDESK:")
        print("1. Copy this cleaned key:")
        print(f"   {result['masked_key']}")
        print("2. Add to backend/.env file:")
        print(f"   OPENAI_API_KEY={result['cleaned_key']}")
        print("3. Restart InLegalDesk backend")
        print("4. API should work properly")
        print()
    
    print(f"📊 Final Status: {result['final_status']}")
    
    # Save cleaned key to file if valid
    if result["is_valid"]:
        try:
            with open("cleaned_api_key.txt", "w") as f:
                f.write(result["cleaned_key"])
            print("\n💾 Cleaned API key saved to: cleaned_api_key.txt")
        except Exception as e:
            print(f"\n⚠️  Could not save to file: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    input("\nPress Enter to exit...")