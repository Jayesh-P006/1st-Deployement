import requests
import json
from flask import current_app

API_BASE = 'https://api.linkedin.com/v2'

def check_linkedin_account_status():
    """Check if LinkedIn credentials are valid and return account info"""
    token = current_app.config.get('LINKEDIN_ACCESS_TOKEN')
    org_id = current_app.config.get('LINKEDIN_ORGANIZATION_ID')
    
    if not token:
        return {
            'status': 'error',
            'message': 'LinkedIn access token not configured',
            'configured': False
        }
    
    try:
        # Verify token by getting user info
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'https://api.linkedin.com/v2/me',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Get localized name
            first_name = data.get('localizedFirstName', '')
            last_name = data.get('localizedLastName', '')
            full_name = f"{first_name} {last_name}".strip()
            
            return {
                'status': 'connected',
                'configured': True,
                'account_id': data.get('id'),
                'name': full_name or 'LinkedIn User',
                'profile_url': f"https://www.linkedin.com/in/{data.get('vanityName', '')}" if data.get('vanityName') else None
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('message', response.text)
            return {
                'status': 'error',
                'configured': True,
                'message': f'Invalid credentials: {error_msg}'
            }
    except requests.exceptions.Timeout:
        return {
            'status': 'error',
            'configured': True,
            'message': 'Connection timeout - check network'
        }
    except Exception as e:
        return {
            'status': 'error',
            'configured': True,
            'message': str(e)
        }

def post_to_linkedin(post):
    token = current_app.config.get('LINKEDIN_ACCESS_TOKEN')
    org_id = current_app.config.get('LINKEDIN_ORGANIZATION_ID')
    if not token:
        raise ValueError('LinkedIn access token not configured. Please set LINKEDIN_ACCESS_TOKEN in config.')

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Parse image paths if available
    image_paths = []
    if post.image_path:
        try:
            image_paths = json.loads(post.image_path) if post.image_path.startswith('[') else [post.image_path]
        except (json.JSONDecodeError, AttributeError):
            image_paths = [post.image_path] if post.image_path else []
    
    # Post with or without images
    if not image_paths:
        # Text-only post
        body = {
            "author": f"urn:li:organization:{org_id}" if org_id else f"urn:li:person:me",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post.content},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
    else:
        # Post with images (requires image upload flow - simplified here)
        # In production, you'd upload images first and get media URNs
        media_items = []
        for img_path in image_paths[:10]:  # LinkedIn supports up to 10 images
            # Simplified: In real implementation, upload each image to LinkedIn's upload API
            # and get the digitalmediaAsset URN, then add to media array
            media_items.append({
                "status": "READY",
                "description": {"text": "Image"},
                "media": f"urn:li:digitalmediaAsset:placeholder_{img_path}",
                "title": {"text": "Image"}
            })
        
        body = {
            "author": f"urn:li:organization:{org_id}" if org_id else f"urn:li:person:me",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post.content},
                    "shareMediaCategory": "IMAGE",
                    "media": media_items
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
    
    try:
        resp = requests.post(f"{API_BASE}/ugcPosts", json=body, headers=headers, timeout=30)
        if resp.status_code >= 300:
            error_data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {'message': resp.text}
            error_msg = error_data.get('message', error_data.get('error', resp.text))
            raise RuntimeError(f'LinkedIn post failed (HTTP {resp.status_code}): {error_msg}')
    except requests.exceptions.Timeout:
        raise RuntimeError('LinkedIn API request timed out. Please check your network connection and try again.')
    except requests.exceptions.ConnectionError:
        raise RuntimeError('Failed to connect to LinkedIn API. Please check your network connection.')
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f'LinkedIn API request failed: {str(e)}')
    
    # LinkedIn typically counts 1 token per API call
    return 1
