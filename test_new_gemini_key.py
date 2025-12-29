"""
Test script to verify if your NEW Gemini API key works
Run this locally with: python test_new_gemini_key.py
"""
import os
import sys

# Prompt user for NEW API key
print("="*60)
print("GEMINI API KEY TESTER")
print("="*60)
print("\nThis will test if your NEW Gemini API key works.")
print("Get a NEW key from: https://aistudio.google.com/app/apikey")
print("\nIMPORTANT: Create a NEW Google Cloud project first!")
print("="*60)

new_api_key = input("\nPaste your NEW Gemini API key here: ").strip()

if not new_api_key:
    print("❌ No API key provided!")
    sys.exit(1)

print("\n🔄 Testing API key...")

try:
    import google.generativeai as genai
    
    # Configure with NEW key
    genai.configure(api_key=new_api_key)
    
    # List available models
    print("\n📋 Available models:")
    models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            models.append(m.name)
            print(f"  ✓ {m.name}")
    
    if not models:
        print("❌ No models available with this key!")
        sys.exit(1)
    
    # Test with a simple generation
    print("\n🧪 Testing content generation...")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    response = model.generate_content("Say 'Hello! API is working!' if you can read this.")
    
    print(f"\n✅ SUCCESS! API Response:")
    print(f"   {response.text}")
    
    print("\n" + "="*60)
    print("✅ YOUR NEW API KEY WORKS!")
    print("="*60)
    print("\nNow update it in Railway:")
    print(f"\n  railway variables --set GEMINI_API_KEY={new_api_key}")
    print("\nOr set it in Railway Dashboard:")
    print("  1. Go to your Railway project")
    print("  2. Click on your service")
    print("  3. Go to 'Variables' tab")
    print("  4. Update GEMINI_API_KEY")
    print("="*60)
    
except Exception as e:
    error_str = str(e)
    print(f"\n❌ ERROR: {error_str}")
    
    if '429' in error_str or 'quota' in error_str.lower():
        print("\n⚠️  QUOTA ISSUE DETECTED!")
        print("This API key has exhausted its quota.")
        print("\nPossible causes:")
        print("  1. This is the SAME old API key (not new)")
        print("  2. You already used this key today")
        print("  3. The free tier quota hasn't reset yet")
        print("\nSolutions:")
        print("  1. Create a BRAND NEW Google Cloud project")
        print("  2. Generate a NEW API key from that project")
        print("  3. Wait until tomorrow for quota reset")
        print("  4. Upgrade to a paid plan")
    elif '403' in error_str or 'API key not valid' in error_str:
        print("\n⚠️  INVALID API KEY!")
        print("This API key is not valid or not activated.")
        print("\nSteps:")
        print("  1. Go to https://aistudio.google.com/app/apikey")
        print("  2. Create a NEW API key")
        print("  3. Make sure Gemini API is enabled")
    else:
        print("\n⚠️  UNKNOWN ERROR")
        print("Check your internet connection and try again.")
    
    sys.exit(1)
