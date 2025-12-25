import requests
import json
from flask import current_app

API_BASE = 'https://graph.facebook.com/v19.0'

def check_instagram_account_status():
    """Check if Instagram credentials are valid and return account info"""
    token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
    business_id = current_app.config.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if not token or not business_id:
        return {
            'status': 'error',
            'message': 'Instagram credentials not configured',
            'configured': False
        }
    
    try:
        # Verify the business account exists and token is valid
        response = requests.get(
            f"{API_BASE}/{business_id}",
            params={
                'fields': 'id,username,name,profile_picture_url',
                'access_token': token
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'connected',
                'configured': True,
                'account_id': data.get('id'),
                'username': data.get('username'),
                'name': data.get('name'),
                'profile_picture': data.get('profile_picture_url')
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('error', {}).get('message', response.text)
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

def post_to_instagram(post):
    token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
    business_id = current_app.config.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    if not token or not business_id:
        raise ValueError('Instagram credentials not configured. Please set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID in config.')
    
    if not post.image_path:
        raise ValueError('Instagram post requires at least one image. Please upload an image before posting.')
    
    # Parse image paths (can be JSON array or single path)
    try:
        image_paths = json.loads(post.image_path) if post.image_path.startswith('[') else [post.image_path]
    except (json.JSONDecodeError, AttributeError) as e:
        raise ValueError(f'Invalid image path format: {str(e)}')
    
    if not image_paths:
        raise ValueError('Instagram post requires at least one image.')
    
    # Verify image files exist
    import os
    for img_path in image_paths:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f'Image file not found: {img_path}. Please upload the image again.')
    
    # Single image post
    if len(image_paths) == 1:
        media_endpoint = f"{API_BASE}/{business_id}/media"
        
        # Instagram requires a publicly accessible image URL
        # Convert local file path to public URL
        import os
        filename = os.path.basename(image_paths[0])
        public_url = current_app.config.get('PUBLIC_URL', 'http://127.0.0.1:5000')
        image_url = f"{public_url}/uploads/{filename}"
        
        data = {
            'image_url': image_url,
            'caption': post.content,
            'access_token': token
        }
        resp = requests.post(media_endpoint, data=data, timeout=30)
        if resp.status_code >= 300:
            error_data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {'message': resp.text}
            error_msg = error_data.get('error', {}).get('message', error_data.get('message', resp.text))
            raise RuntimeError(f'Instagram media create failed (HTTP {resp.status_code}): {error_msg}')
        creation_id = resp.json().get('id')
        if not creation_id:
            raise RuntimeError('No creation id returned from Instagram API. Response: ' + str(resp.json()))
    else:
        # Carousel post with multiple images
        media_ids = []
        for img_path in image_paths:
            media_endpoint = f"{API_BASE}/{business_id}/media"
            
            # Convert local file path to public URL
            import os
            filename = os.path.basename(img_path)
            public_url = current_app.config.get('PUBLIC_URL', 'http://127.0.0.1:5000')
            image_url = f"{public_url}/uploads/{filename}"
            
            data = {
                'image_url': image_url,
                'is_carousel_item': 'true',
                'access_token': token
            }
            resp = requests.post(media_endpoint, data=data, timeout=30)
            if resp.status_code >= 300:
                error_data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {'message': resp.text}
                error_msg = error_data.get('error', {}).get('message', error_data.get('message', resp.text))
                raise RuntimeError(f'Instagram carousel item create failed (HTTP {resp.status_code}): {error_msg}')
            media_id = resp.json().get('id')
            if media_id:
                media_ids.append(media_id)
        
        # Create carousel container
        carousel_endpoint = f"{API_BASE}/{business_id}/media"
        carousel_data = {
            'media_type': 'CAROUSEL',
            'children': ','.join(media_ids),
            'caption': post.content,
            'access_token': token
        }
        carousel_resp = requests.post(carousel_endpoint, data=carousel_data, timeout=30)
        if carousel_resp.status_code >= 300:
            error_data = carousel_resp.json() if carousel_resp.headers.get('content-type', '').startswith('application/json') else {'message': carousel_resp.text}
            error_msg = error_data.get('error', {}).get('message', error_data.get('message', carousel_resp.text))
            raise RuntimeError(f'Instagram carousel create failed (HTTP {carousel_resp.status_code}): {error_msg}')
        creation_id = carousel_resp.json().get('id')
        if not creation_id:
            raise RuntimeError('No creation id returned from Instagram carousel. Response: ' + str(carousel_resp.json()))
    
    # Publish media
    publish_endpoint = f"{API_BASE}/{business_id}/media_publish"
    pub_resp = requests.post(publish_endpoint, data={'creation_id': creation_id, 'access_token': token}, timeout=30)
    if pub_resp.status_code >= 300:
        error_data = pub_resp.json() if pub_resp.headers.get('content-type', '').startswith('application/json') else {'message': pub_resp.text}
        error_msg = error_data.get('error', {}).get('message', error_data.get('message', pub_resp.text))
        raise RuntimeError(f'Instagram publish failed (HTTP {pub_resp.status_code}): {error_msg}')
    
    # Instagram Graph API typically counts 1 token per post
    return 1
