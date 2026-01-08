"""
Diagnostic script for Instagram publishing issues
Tests the complete flow to identify where the problem is
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_instagram_publishing():
    """Test complete Instagram publishing flow"""
    
    print("=" * 80)
    print("Instagram Publishing Diagnostic Report")
    print("=" * 80)
    
    issues = []
    warnings = []
    success_checks = []
    
    # 1. Check Credentials
    print("\n✓ STEP 1: Checking Instagram Credentials")
    print("-" * 80)
    
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
    business_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')
    
    if not access_token:
        issues.append("❌ INSTAGRAM_ACCESS_TOKEN is not set")
    else:
        success_checks.append("✓ INSTAGRAM_ACCESS_TOKEN is set")
        
    if not business_id:
        issues.append("❌ INSTAGRAM_BUSINESS_ACCOUNT_ID is not set")
    else:
        success_checks.append("✓ INSTAGRAM_BUSINESS_ACCOUNT_ID is set")
    
    # 2. Check PUBLIC_URL
    print("\n✓ STEP 2: Checking PUBLIC_URL Configuration")
    print("-" * 80)
    
    public_url = os.getenv('PUBLIC_URL', '')
    railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
    
    if not public_url and not railway_domain:
        issues.append("❌ PUBLIC_URL and RAILWAY_PUBLIC_DOMAIN are not set")
    else:
        final_url = public_url or f"https://{railway_domain}"
        print(f"Using URL: {final_url}")
        
        if 'localhost' in final_url or '127.0.0.1' in final_url:
            issues.append(f"❌ URL is localhost: {final_url}")
        elif not final_url.startswith('https://'):
            issues.append(f"❌ URL is not HTTPS: {final_url}")
        else:
            success_checks.append(f"✓ PUBLIC_URL is valid: {final_url}")
    
    # 3. Test Image File Existence
    print("\n✓ STEP 3: Checking Uploads Folder")
    print("-" * 80)
    
    uploads_folder = os.path.join(os.path.dirname(__file__), 'uploads')
    
    if os.path.exists(uploads_folder):
        files = [f for f in os.listdir(uploads_folder) if os.path.isfile(os.path.join(uploads_folder, f))]
        if files:
            success_checks.append(f"✓ Uploads folder exists with {len(files)} file(s)")
            print(f"Files in uploads folder:")
            for f in files[:5]:  # Show first 5 files
                file_path = os.path.join(uploads_folder, f)
                file_size = os.path.getsize(file_path)
                print(f"  - {f} ({file_size} bytes)")
        else:
            warnings.append("⚠️ Uploads folder is empty")
    else:
        warnings.append("⚠️ Uploads folder does not exist")
    
    # 4. Test Image URL Accessibility
    print("\n✓ STEP 4: Testing Image URL Accessibility")
    print("-" * 80)
    
    if public_url or railway_domain:
        final_url = public_url or f"https://{railway_domain}"
        
        # Try to access the uploads endpoint
        test_url = f"{final_url.rstrip('/')}/uploads/"
        print(f"Testing URL: {test_url}")
        
        try:
            response = requests.head(test_url, timeout=10, allow_redirects=True)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code < 500:
                success_checks.append(f"✓ Uploads endpoint is accessible (status: {response.status_code})")
            else:
                warnings.append(f"⚠️ Uploads endpoint returned error: {response.status_code}")
        except requests.exceptions.Timeout:
            issues.append(f"❌ Uploads endpoint timeout - URL may not be accessible")
        except requests.exceptions.RequestException as e:
            issues.append(f"❌ Cannot reach uploads endpoint: {str(e)}")
    
    # 5. Test Instagram API Connection
    print("\n✓ STEP 5: Testing Instagram API Connection")
    print("-" * 80)
    
    if access_token and business_id:
        try:
            api_url = f"https://graph.facebook.com/v19.0/{business_id}"
            print(f"Testing: {api_url}")
            
            response = requests.get(
                api_url,
                params={
                    'fields': 'id,username,name',
                    'access_token': access_token
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                success_checks.append(f"✓ Connected to Instagram: @{data.get('username', 'unknown')}")
                print(f"Account: {data.get('name', 'N/A')}")
                print(f"Username: @{data.get('username', 'N/A')}")
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', response.text)
                issues.append(f"❌ Instagram API Error ({response.status_code}): {error_msg}")
                print(f"Error: {error_msg}")
        except requests.exceptions.Timeout:
            issues.append("❌ Instagram API timeout - network issue")
        except Exception as e:
            issues.append(f"❌ Instagram API error: {str(e)}")
    
    # 6. Test Media Creation (without actually publishing)
    print("\n✓ STEP 6: Testing Instagram Media Creation")
    print("-" * 80)
    
    if access_token and business_id and (public_url or railway_domain):
        final_url = public_url or f"https://{railway_domain}"
        
        # Create a test image URL
        test_image_url = f"{final_url.rstrip('/')}/uploads/test.jpg"
        print(f"Test Image URL: {test_image_url}")
        
        try:
            media_endpoint = f"https://graph.facebook.com/v19.0/{business_id}/media"
            
            test_data = {
                'image_url': test_image_url,
                'caption': 'Test post from diagnostic script',
                'access_token': access_token
            }
            
            response = requests.post(media_endpoint, data=test_data, timeout=30)
            
            if response.status_code == 200:
                success_checks.append("✓ Can create media in Instagram (test passed)")
            elif response.status_code == 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', response.text)
                
                if 'Media ID' in error_msg or 'not available' in error_msg:
                    issues.append(f"❌ Image URL is not accessible: {error_msg}")
                    print(f"This means Instagram cannot download your image from: {test_image_url}")
                else:
                    issues.append(f"❌ Media creation failed: {error_msg}")
            else:
                issues.append(f"❌ Media creation failed ({response.status_code})")
                print(f"Response: {response.text}")
        except Exception as e:
            warnings.append(f"⚠️ Could not test media creation: {str(e)}")
    
    # Print Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if success_checks:
        print("\n✅ WORKING:")
        for check in success_checks:
            print(f"  {check}")
    
    if issues:
        print("\n❌ CRITICAL ISSUES:")
        for issue in issues:
            print(f"  {issue}")
    
    if warnings:
        print("\n⚠️ WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if any("Media ID" in issue for issue in issues):
        print("\n🔍 The 'Media ID is not available' error means Instagram cannot access your image.")
        print("\nSOLUTION:")
        print("1. Verify PUBLIC_URL is set to your deployed domain (e.g., https://your-app.up.railway.app)")
        print("2. Make sure the domain is HTTPS (Instagram requirement)")
        print("3. Test if you can access your image URL in a browser")
        print("4. Check if the /uploads route is working: https://your-domain/uploads/")
        print("5. Ensure image files exist in the uploads folder")
        print("6. Restart your Railway app after setting environment variables")
    
    if any("localhost" in issue or "127.0.0.1" in issue for issue in issues):
        print("\n🌐 Your PUBLIC_URL is pointing to localhost.")
        print("\nSOLUTION:")
        print("1. Go to Railway → Your Service → Variables")
        print("2. Set PUBLIC_URL to your deployed domain: https://your-app.up.railway.app")
        print("3. Redeploy your application")
    
    if any("INSTAGRAM_ACCESS_TOKEN" in issue for issue in issues):
        print("\n🔑 Instagram credentials are missing.")
        print("\nSOLUTION:")
        print("1. Go to https://developers.facebook.com/")
        print("2. Create a new access token with instagram_business_content_publish scope")
        print("3. Set INSTAGRAM_ACCESS_TOKEN in Railway environment variables")
        print("4. Redeploy your application")
    
    print("\n" + "=" * 80)
    
    return len(issues) == 0

if __name__ == '__main__':
    success = test_instagram_publishing()
    sys.exit(0 if success else 1)
