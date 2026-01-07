"""
Helper utilities for media URLs and downloads.

- convert_to_direct_url: Converts sharing links to direct download URLs
- download_image_to_uploads: Downloads an image URL into the uploads folder
"""

import os
import mimetypes
from datetime import datetime
from typing import Optional

import requests

def convert_to_direct_url(url):
    """
    Convert various image hosting URLs to direct download URLs
    
    Supports:
    - Google Drive
    - Dropbox
    - OneDrive
    - Direct URLs
    """
    
    # Google Drive
    if 'drive.google.com' in url:
        # Extract file ID from various Google Drive URL formats
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
        else:
            return url
        return f'https://drive.google.com/uc?export=download&id={file_id}'
    
    # Dropbox
    elif 'dropbox.com' in url:
        return url.replace('www.dropbox.com', 'dl.dropboxusercontent.com').replace('?dl=0', '?dl=1')
    
    # OneDrive
    elif 'onedrive.live.com' in url or '1drv.ms' in url:
        # OneDrive requires more complex handling
        return url.replace('view.aspx', 'download.aspx')
    
    # Already a direct URL
    else:
        return url


def download_image_to_uploads(image_url: str, upload_folder: str) -> Optional[str]:
    """
    Download an image from a URL into the upload folder and return the full path.

    - Converts common share URLs (Drive/Dropbox/OneDrive) to direct links
    - Validates that the response looks like an image
    - Picks a reasonable file extension
    """
    if not image_url:
        return None

    os.makedirs(upload_folder, exist_ok=True)

    direct_url = convert_to_direct_url(image_url.strip())
    try:
        resp = requests.get(direct_url, timeout=15, stream=True)
        resp.raise_for_status()
    except Exception:
        return None

    content_type = resp.headers.get('Content-Type', '')
    if not content_type.startswith('image/'):
        return None

    # Determine extension from content-type or URL
    ext = mimetypes.guess_extension(content_type.split(';')[0].strip()) or ''
    if not ext:
        # Try from URL path
        guessed = os.path.splitext(direct_url.split('?')[0])[1]
        ext = guessed if guessed else '.jpg'

    filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + 'remote' + ext
    full_path = os.path.join(upload_folder, filename)

    try:
        with open(full_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except Exception:
        return None

    return full_path


if __name__ == '__main__':
    # Test examples
    test_urls = [
        'https://drive.google.com/file/d/1ABC123xyz/view?usp=sharing',
        'https://drive.google.com/open?id=1ABC123xyz',
        'https://www.dropbox.com/s/abc123/image.jpg?dl=0',
        'https://example.com/image.jpg'
    ]
    
    print("URL Conversion Tests:")
    print("=" * 70)
    for url in test_urls:
        converted = convert_to_direct_url(url)
        print(f"\nOriginal:  {url}")
        print(f"Converted: {converted}")
