# Developer Guide - Draft Editor Features

## How to Use the New Features

### 1. AI Caption Generation

**For Users:**
1. Upload at least one image in Step 1
2. Click the "🤖 Generate with AI" button in Step 2
3. Wait 2-3 seconds for AI to analyze images
4. Caption appears automatically in the text area
5. Edit as needed and save

**For Developers:**
```python
# Vision service location
from app.ai.vision_service import analyze_image_for_caption, analyze_multiple_images

# Single image
result = analyze_image_for_caption(
    image_path='/path/to/image.jpg',
    platform='instagram',  # or 'linkedin'
    draft_title='My Post Title'
)

# Multiple images
result = analyze_multiple_images(
    image_paths=['/path/1.jpg', '/path/2.jpg'],
    platform='instagram',
    draft_title='My Carousel Post'
)

# Result format
{
    'success': True,
    'caption': 'Generated caption text...',
    'error': None
}
```

**API Endpoint:**
```javascript
// POST /collab/api/draft/<draft_id>/generate-caption
const response = await fetch(`/collab/api/draft/${draftId}/generate-caption`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
});

const data = await response.json();
// { success: true, caption: "..." }
```

### 2. Real-Time Comments

**For Users:**
- Comments update automatically every 3 seconds
- New comments are highlighted with animation
- No need to refresh the page
- Comment count badge updates in real-time

**For Developers:**
```python
# API endpoint in collab_routes.py
@collab_bp.route('/api/draft/<int:draft_id>/comments', methods=['GET'])
def get_comments(draft_id):
    # Returns JSON with comment list
    pass
```

**Frontend Implementation:**
```javascript
// Auto-refresh every 3 seconds
setInterval(refreshComments, 3000);

async function refreshComments() {
    const response = await fetch(`/collab/api/draft/${draftId}/comments`);
    const data = await response.json();
    
    // Update UI with new comments
    // Highlight new ones with animation
}
```

### 3. Tag Input System

**For Users:**
1. Type @ followed by username
2. Press Enter or Comma to add tag
3. Click × to remove tag
4. Tags are saved as comma-separated values

**For Developers:**
```javascript
// Tag management functions
function addTag(tagText) {
    // Adds @ prefix if missing
    // Prevents duplicates
    // Creates visual chip
}

function removeTag(element) {
    // Removes tag chip
    // Updates hidden input
}

function updateTagsInput() {
    // Syncs visual chips with form input
    const tags = Array.from(document.querySelectorAll('.tag-item'))
        .map(el => el.dataset.tag);
    tagsHiddenInput.value = tags.join(',');
}
```

### 4. Drag and Drop Upload

**For Users:**
- Drag files onto the upload zone
- Or click to browse files
- Visual feedback during drag
- Automatic form submission after drop

**For Developers:**
```javascript
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');  // Visual feedback
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    fileInput.files = e.dataTransfer.files;
    document.getElementById('mediaUploadForm').submit();
});
```

## Environment Variables Needed

```bash
# In Railway or .env file
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash  # Supports vision
```

## Troubleshooting

### AI Caption Generation Not Working

**Check:**
1. GEMINI_API_KEY is set
2. Image was uploaded successfully
3. Image file is accessible by backend
4. Gemini API quota not exceeded
5. Check browser console for errors

**Debug:**
```python
# In vision_service.py, add logging
current_app.logger.info(f'Analyzing image: {image_path}')
current_app.logger.error(f'Vision error: {str(e)}')
```

### Real-Time Comments Not Updating

**Check:**
1. JavaScript console for errors
2. Network tab - API calls every 3s
3. CORS issues (shouldn't happen on same domain)
4. User is logged in

**Debug:**
```javascript
// Check if interval is running
console.log('Refreshing comments...');
```

### Drag and Drop Not Working

**Check:**
1. Browser supports drag and drop (all modern browsers do)
2. File input exists with correct ID
3. Form has enctype="multipart/form-data"

## Performance Optimization Tips

### 1. Image Upload
```python
# Resize images before saving (future enhancement)
from PIL import Image

def resize_image(image_path, max_size=(1920, 1920)):
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    img.save(image_path, optimize=True, quality=85)
```

### 2. Comment Polling
```javascript
// Consider WebSocket for large-scale deployment
const ws = new WebSocket('ws://...');
ws.onmessage = (event) => {
    const comment = JSON.parse(event.data);
    addCommentToUI(comment);
};
```

### 3. AI Generation Caching
```python
# Cache generated captions (future enhancement)
from flask_caching import Cache

@cache.memoize(timeout=3600)
def analyze_image_for_caption(image_path, platform, draft_title):
    # Cache based on image hash + platform
    pass
```

## Testing

### Manual Testing Checklist
- [ ] Upload single image → Generate caption
- [ ] Upload multiple images → Generate caption
- [ ] Add/remove tags
- [ ] Post comment → Verify real-time update
- [ ] Drag and drop file
- [ ] Character counter updates
- [ ] Progress bar reflects completion
- [ ] All buttons show loading states
- [ ] Mobile responsiveness

### Automated Testing (Future)
```python
# test_vision_service.py
def test_analyze_image():
    result = analyze_image_for_caption(
        'tests/fixtures/test_image.jpg',
        'instagram',
        'Test Post'
    )
    assert result['success'] == True
    assert len(result['caption']) > 0
```

## Common Issues & Solutions

### Issue: Gemini API Quota Exceeded
**Solution:** 
- Wait for quota reset (daily)
- Upgrade to paid plan
- Implement fallback messages
- Cache results when possible

### Issue: Large Image Upload Fails
**Solution:**
- Add client-side compression
- Set max file size limit
- Show file size warning
- Implement chunked upload

### Issue: Comments Not Polling
**Solution:**
- Check browser console
- Verify API endpoint is accessible
- Check user authentication
- Restart interval if stopped

## Browser Compatibility

**Supported:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Required Features:**
- Fetch API
- async/await
- CSS Grid
- CSS Custom Properties
- FileReader API

## Security Considerations

1. **File Upload**
   - Validate file types on backend
   - Scan for malware
   - Limit file sizes
   - Sanitize filenames

2. **API Endpoints**
   - Require authentication
   - Rate limiting on AI generation
   - CSRF protection (Flask-WTF)
   - Input validation

3. **Comments**
   - XSS protection (escape HTML)
   - Rate limiting
   - Content moderation

## Monitoring & Analytics

**Key Metrics:**
```python
# Add to logging
logger.info(f'AI caption generated: {draft_id}, time: {response_time}s')
logger.info(f'Comment added: {draft_id}, user: {user_id}')
logger.error(f'Vision API error: {error_message}')
```

**Track in Database:**
- AI caption usage count
- Average generation time
- Success/failure rate
- User adoption rate

---

**Need Help?** Check the code comments or Railway logs for debugging.
