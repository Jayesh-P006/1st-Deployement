# Instagram API Implementation - TODO

## 🔧 Required Implementation

### Location: `app/automation_handlers.py`

The `_post_comment_reply()` function currently has a placeholder implementation. You need to complete it with actual Instagram Graph API integration.

---

## 📝 Current Placeholder Code

```python
def _post_comment_reply(comment_id, reply_text, access_token):
    """
    Post a reply to an Instagram comment using the Graph API
    
    TODO: Implement actual Instagram Graph API call
    Endpoint: POST /{comment-id}/replies
    """
    current_app.logger.warning(f"Comment reply not implemented. Would reply to {comment_id}: {reply_text}")
    return None
```

---

## ✅ Complete Implementation

Replace the placeholder with this code:

```python
import requests

def _post_comment_reply(comment_id, reply_text, access_token):
    """
    Post a reply to an Instagram comment using the Graph API
    
    Args:
        comment_id: Instagram comment ID
        reply_text: Reply message text
        access_token: Instagram access token with instagram_manage_comments permission
    
    Returns:
        dict: API response with comment ID, or None on failure
    """
    url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
    
    payload = {
        'message': reply_text,
        'access_token': access_token
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        current_app.logger.info(f"Successfully posted reply to comment {comment_id}")
        return result
        
    except requests.RequestException as e:
        current_app.logger.error(f"Failed to post comment reply to {comment_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            current_app.logger.error(f"Response: {e.response.text}")
        return None
```

---

## 🔐 Access Token Requirements

### Required Permissions
Your Instagram access token must have:
- `instagram_manage_comments` - Required to reply to comments
- `pages_read_engagement` - To read comment data
- `instagram_basic` - Basic Instagram access

### Getting the Access Token

The access token should be retrieved from your database or environment:

```python
# In _process_auto_comment_reply function:
user = User.query.get(user_id)
if not user:
    return

access_token = user.instagram_access_token  # Adjust based on your User model
```

### Token Storage
Ensure your User model stores Instagram credentials:
```python
class User(db.Model):
    # ... existing fields
    instagram_access_token = db.Column(db.String(500))
    instagram_user_id = db.Column(db.String(100))
    # ...
```

---

## 📡 API Endpoint Documentation

### POST /{comment-id}/replies

**Endpoint:** `https://graph.facebook.com/v19.0/{comment-id}/replies`

**Parameters:**
- `message` (string, required) - Reply text (max 2,200 characters)
- `access_token` (string, required) - Page or User access token

**Response:**
```json
{
  "id": "1234567890_1234567890"
}
```

**Error Response:**
```json
{
  "error": {
    "message": "Error description",
    "type": "OAuthException",
    "code": 190
  }
}
```

---

## 🧪 Testing Steps

### 1. Test Comment Reply in Isolation

Create a test script `test_comment_reply.py`:

```python
import requests
import os

def test_comment_reply():
    comment_id = "YOUR_TEST_COMMENT_ID"  # Get from webhook or Graph API
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    
    url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
    
    payload = {
        'message': 'Test reply from automation!',
        'access_token': access_token
    }
    
    response = requests.post(url, data=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == '__main__':
    test_comment_reply()
```

### 2. Test Through Webhook

1. Enable auto-comment in UI: `/automations/auto-comment`
2. Post a comment on your Instagram post
3. Check logs at `/automations/logs`
4. Verify reply appears on Instagram

---

## ⚠️ Common Issues

### Issue 1: Permission Error
```json
{
  "error": {
    "message": "Permissions error",
    "code": 200
  }
}
```

**Solution:** Regenerate access token with `instagram_manage_comments` permission.

### Issue 2: Invalid Comment ID
```json
{
  "error": {
    "message": "Invalid parameter",
    "code": 100
  }
}
```

**Solution:** Verify comment_id format. Instagram comment IDs look like: `17843XXXXXXX_17843XXXXXXX`

### Issue 3: Rate Limiting
```json
{
  "error": {
    "message": "API rate limit exceeded",
    "code": 4
  }
}
```

**Solution:** Reduce `rate_limit_per_hour` in Auto-Comment settings.

---

## 🔍 Debugging Checklist

- [ ] `requests` library imported in automation_handlers.py
- [ ] Access token retrieved from User model
- [ ] Access token has correct permissions
- [ ] Comment ID format is valid (from webhook)
- [ ] API endpoint URL is correct (v19.0)
- [ ] Error responses are logged
- [ ] Network timeout set appropriately (10s recommended)
- [ ] Test with a real Instagram post and comment

---

## 📊 Integration with Existing Code

### Current Flow:
```
Instagram Comment Webhook
    ↓
handle_webhook_event() [instagram_webhooks.py]
    ↓
handle_comment_event() [automation_handlers.py]
    ↓
_process_auto_comment_reply() [threaded]
    ↓
_post_comment_reply() ← YOU ARE HERE (needs implementation)
    ↓
AutomationLog created
```

### After Implementation:
```
Instagram Comment Webhook
    ↓
handle_webhook_event() [instagram_webhooks.py]
    ↓
handle_comment_event() [automation_handlers.py]
    ↓
_process_auto_comment_reply() [threaded]
    ↓
_post_comment_reply() ← Fully implemented ✅
    ↓
Reply posted on Instagram ✅
    ↓
AutomationLog created ✅
```

---

## 🎯 Next Steps

1. **Add requests import** if not already present:
   ```python
   import requests
   ```

2. **Replace placeholder function** with complete implementation above

3. **Verify User model** has instagram_access_token field

4. **Test API call** with test script before enabling automation

5. **Monitor logs** at `/automations/logs` for any errors

6. **Adjust rate limits** in auto-comment settings based on testing

---

## 📞 Instagram Graph API Resources

- [Comment Replies Documentation](https://developers.facebook.com/docs/instagram-api/reference/ig-comment/replies)
- [Permissions Reference](https://developers.facebook.com/docs/permissions/reference)
- [Error Codes Reference](https://developers.facebook.com/docs/graph-api/using-graph-api/error-handling)
- [Rate Limit Documentation](https://developers.facebook.com/docs/graph-api/overview/rate-limiting)

---

**Once implemented, your auto-comment automation will be fully operational!** 🚀
