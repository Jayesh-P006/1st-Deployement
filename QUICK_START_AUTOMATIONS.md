# ⚡ Quick Start - Automations Suite

## 🚀 Get Your Automations Running in 5 Steps

---

## Step 1: Run Database Migration ⏱️ 2 minutes

Open PowerShell in your project directory:

```powershell
cd "c:\Jayesh\Deployement ready"

# Create the migration
flask db migrate -m "Add automation models"

# Apply the migration
flask db upgrade
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, Add automation models
```

✅ **Verification:** Check that 4 new tables exist:
- `auto_reply_settings`
- `comment_trigger`
- `comment_dm_tracker`
- `automation_log`

---

## Step 2: Configure Instagram Webhooks ⏱️ 5 minutes

1. Go to [Meta for Developers](https://developers.facebook.com/apps/)
2. Select your app
3. Navigate to **Products** → **Webhooks**
4. Find your Instagram subscription
5. Click **Edit**
6. ✅ Check the **comments** field
7. Click **Save**

**Test the webhook:**
```powershell
# In a separate terminal, monitor your logs
flask run
```

Post a comment on your Instagram and watch for webhook events in logs.

---

## Step 3: Implement Instagram API (CRITICAL) ⏱️ 10 minutes

Open [automation_handlers.py](app/automation_handlers.py) and find the `_post_comment_reply` function.

**Replace this:**
```python
def _post_comment_reply(comment_id, reply_text, access_token):
    """
    TODO: Implement actual Instagram Graph API call
    """
    current_app.logger.warning(f"Comment reply not implemented...")
    return None
```

**With this:**
```python
import requests  # Add at top of file if not present

def _post_comment_reply(comment_id, reply_text, access_token):
    """Post a reply to an Instagram comment using the Graph API"""
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
        current_app.logger.error(f"Failed to post comment reply: {e}")
        if hasattr(e, 'response') and e.response is not None:
            current_app.logger.error(f"Response: {e.response.text}")
        return None
```

💡 **Note:** Ensure your access token has `instagram_manage_comments` permission!

---

## Step 4: Configure Your First Automation ⏱️ 5 minutes

### Option A: Auto-Comment Replies

1. Start your app: `flask run`
2. Navigate to http://localhost:5000/automations
3. Click **💬 Auto-Comment Replies**
4. Configure:
   - ✅ Enable for Instagram
   - ✅ Enable RAG (for intelligent responses)
   - Set fallback: "Thanks for your comment! 🙏"
   - Choose tone: Friendly
   - Response delay: 5 seconds
   - Rate limit: 20 per hour
5. Click **Save Settings**

### Option B: Comment-to-DM

1. Navigate to http://localhost:5000/automations
2. Click **📨 Comment-to-DM**
3. Add a trigger:
   - Keyword: `DM ME`
   - Message: `Check your DMs for something special! 🎁`
   - ✅ Enable RAG (optional)
   - ✅ Active
4. Click **Add Trigger**

---

## Step 5: Test Everything ⏱️ 5 minutes

### Test Auto-Comment:
1. Post a comment on your Instagram post
2. Wait 5-10 seconds
3. Check if auto-reply appears on Instagram
4. Verify in logs: http://localhost:5000/automations/logs

### Test Comment-to-DM:
1. Comment "DM ME" on your Instagram post
2. Check your Instagram DMs
3. Verify in logs: http://localhost:5000/automations/logs

---

## 🎯 Checklist

### Pre-Deployment
- [ ] Database migration completed successfully
- [ ] Instagram webhook configured for comments field
- [ ] `_post_comment_reply()` function implemented
- [ ] Access token has correct permissions
- [ ] `requests` library imported

### First Test
- [ ] Flask app running without errors
- [ ] Can access /automations dashboard
- [ ] Auto-comment settings page loads
- [ ] Comment-to-DM page loads
- [ ] Logs page accessible

### Live Test
- [ ] Posted test comment on Instagram
- [ ] Webhook received in Flask logs
- [ ] Automation triggered successfully
- [ ] Reply/DM sent successfully
- [ ] Activity logged at /automations/logs

---

## 🐛 Quick Troubleshooting

### No webhook events received?
```powershell
# Check if webhook is properly configured
# Verify callback URL is accessible
# Check Flask logs for incoming requests
```

### Auto-reply not posting?
- Check `_post_comment_reply()` is implemented
- Verify access token permissions
- Review logs at `/automations/logs`
- Check Instagram API rate limits

### RAG not working?
- Verify RAG system is operational: `/rag/status`
- Check fallback message is configured
- Review error logs

### DMs not sending?
- Verify existing DM functionality works
- Check Instagram token permissions
- Review `automation_log` table for errors

---

## 📊 Success Indicators

### You're good to go when you see:
- ✅ Green status on dashboard
- ✅ Automation logs showing successful operations
- ✅ Instagram replies appearing automatically
- ✅ DMs being sent for triggers
- ✅ No errors in Flask logs

---

## 📚 Need More Help?

Detailed guides:
- **Complete Guide:** [AUTOMATIONS_SUITE_GUIDE.md](AUTOMATIONS_SUITE_GUIDE.md)
- **API Implementation:** [INSTAGRAM_API_TODO.md](INSTAGRAM_API_TODO.md)
- **Summary:** [AUTOMATIONS_COMPLETE.md](AUTOMATIONS_COMPLETE.md)

---

## 🎉 That's It!

Your Automations Suite is now fully operational. Time to automate your Instagram engagement! 🚀

**Total Setup Time:** ~30 minutes
**Value:** Unlimited automated engagement ♾️

---

**Pro Tips:**
- Start with conservative rate limits
- Monitor logs frequently in first 24 hours
- Adjust RAG settings based on response quality
- Create multiple triggers for different use cases
- Review analytics weekly to optimize

**Happy Automating! 🎊**
