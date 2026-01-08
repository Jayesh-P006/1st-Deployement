"""
Script to verify Instagram publishing configuration
Run this before attempting to publish posts to Instagram
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('.env')

def verify_config():
    """Check all required configurations for Instagram publishing"""
    
    print("=" * 70)
    print("Instagram Configuration Verification")
    print("=" * 70)
    
    issues = []
    warnings = []
    
    # 1. Check Instagram credentials
    print("\n1. Checking Instagram Credentials...")
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
    business_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')
    
    if not access_token:
        issues.append("❌ INSTAGRAM_ACCESS_TOKEN is not set")
    else:
        print(f"   ✓ INSTAGRAM_ACCESS_TOKEN: {access_token[:20]}...")
    
    if not business_id:
        issues.append("❌ INSTAGRAM_BUSINESS_ACCOUNT_ID is not set")
    else:
        print(f"   ✓ INSTAGRAM_BUSINESS_ACCOUNT_ID: {business_id}")
    
    # 2. Check PUBLIC_URL configuration
    print("\n2. Checking PUBLIC_URL Configuration...")
    public_url = os.getenv('PUBLIC_URL', '')
    railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
    railway_static = os.getenv('RAILWAY_STATIC_URL', '')
    
    if not public_url and not railway_domain and not railway_static:
        issues.append("❌ PUBLIC_URL, RAILWAY_PUBLIC_DOMAIN, or RAILWAY_STATIC_URL must be set")
        print("   ❌ No public URL configured")
    else:
        # Determine which one is being used
        if public_url:
            print(f"   ✓ PUBLIC_URL: {public_url}")
        elif railway_static:
            print(f"   ✓ RAILWAY_STATIC_URL: {railway_static}")
            public_url = railway_static
        elif railway_domain:
            print(f"   ✓ RAILWAY_PUBLIC_DOMAIN: {railway_domain}")
            public_url = f"https://{railway_domain}"
        
        # Validate URL format
        if public_url:
            if 'localhost' in public_url or '127.0.0.1' in public_url:
                issues.append("❌ PUBLIC_URL points to localhost - Instagram cannot access local URLs")
                print("   ❌ URL is localhost (not accessible by Instagram)")
            elif not public_url.startswith('https://'):
                issues.append("❌ PUBLIC_URL must use HTTPS (Instagram requirement)")
                print("   ❌ URL does not use HTTPS")
            else:
                print("   ✓ URL format is valid")
                
                # Test if URL is accessible
                print("\n3. Testing Public URL Accessibility...")
                try:
                    test_url = f"{public_url.rstrip('/')}/uploads/"
                    response = requests.head(test_url, timeout=10)
                    if response.status_code < 500:
                        print(f"   ✓ URL is accessible (status: {response.status_code})")
                    else:
                        warnings.append(f"⚠️  URL returned status {response.status_code}")
                        print(f"   ⚠️  URL returned status {response.status_code}")
                except requests.exceptions.RequestException as e:
                    warnings.append(f"⚠️  Could not reach URL: {str(e)}")
                    print(f"   ⚠️  Could not reach URL: {str(e)}")
    
    # 4. Check uploads folder
    print("\n4. Checking Uploads Folder...")
    if os.path.exists('uploads'):
        file_count = len([f for f in os.listdir('uploads') if os.path.isfile(os.path.join('uploads', f))])
        print(f"   ✓ Uploads folder exists with {file_count} file(s)")
    else:
        warnings.append("⚠️  Uploads folder does not exist (will be created automatically)")
        print("   ⚠️  Uploads folder does not exist")
    
    # 5. Test Instagram API connection
    if access_token and business_id:
        print("\n5. Testing Instagram API Connection...")
        try:
            response = requests.get(
                f"https://graph.facebook.com/v19.0/{business_id}",
                params={
                    'fields': 'id,username',
                    'access_token': access_token
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Connected to Instagram account: @{data.get('username', 'unknown')}")
            else:
                issues.append(f"❌ Instagram API returned error: {response.text}")
                print(f"   ❌ API Error: {response.text}")
        except Exception as e:
            warnings.append(f"⚠️  Could not test API: {str(e)}")
            print(f"   ⚠️  Could not test API: {str(e)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    if not issues and not warnings:
        print("✅ All checks passed! Your Instagram configuration is ready.")
    else:
        if issues:
            print("\n❌ CRITICAL ISSUES (must fix):")
            for issue in issues:
                print(f"   {issue}")
        if warnings:
            print("\n⚠️  WARNINGS (recommended to fix):")
            for warning in warnings:
                print(f"   {warning}")
    
    print("\n" + "=" * 70)
    
    # Provide solutions
    if issues:
        print("\n🔧 How to Fix:")
        print("-" * 70)
        
        if any('PUBLIC_URL' in issue for issue in issues):
            print("\nFor Railway Deployment:")
            print("1. Go to your Railway project dashboard")
            print("2. Click on your service → Variables tab")
            print("3. Add one of these variables:")
            print("   - PUBLIC_URL = https://your-app.up.railway.app")
            print("   - RAILWAY_PUBLIC_DOMAIN = your-app.up.railway.app")
            print("\nFor Local Testing:")
            print("1. Install ngrok: https://ngrok.com/download")
            print("2. Run: ngrok http 5000")
            print("3. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
            print("4. Set in .env: PUBLIC_URL=https://abc123.ngrok.io")
        
        if any('INSTAGRAM' in issue for issue in issues):
            print("\nFor Instagram Credentials:")
            print("1. Go to Meta Developers: https://developers.facebook.com/")
            print("2. Get your Instagram Business Account ID and Access Token")
            print("3. Set in Railway or .env:")
            print("   - INSTAGRAM_ACCESS_TOKEN=your_token")
            print("   - INSTAGRAM_BUSINESS_ACCOUNT_ID=your_id")
        
        print("=" * 70)

if __name__ == '__main__':
    verify_config()
