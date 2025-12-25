"""
Helper function to convert Google Drive links to direct download URLs
"""

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
