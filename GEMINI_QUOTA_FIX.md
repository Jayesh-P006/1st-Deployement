# Gemini API Quota Fix - Applied Changes

## Problems Identified

1. **Test script calling API continuously** - `test_webhook.py` was making actual Gemini API calls every time it ran
2. **No message age check** - System was trying to reply to old messages repeatedly
3. **No cooldown period** - Same conversation could trigger multiple API calls quickly

## Changes Made

### 1. Disabled Gemini Test in `test_webhook.py`
- Changed `test_gemini_api()` to only check if API key is set
- Removed actual API call that was consuming quota
- Now shows: "Skipping actual API test to preserve quota"

### 2. Added Message Age Check in `gemini_service.py`
- Added 5-minute cutoff for auto-replies
- Messages older than 5 minutes will not trigger auto-reply
- Prevents replying to old/stale messages

### 3. Added Duplicate Message Protection
- Already existed in `instagram_webhooks.py` line 251
- Uses `_normalize_message_id()` to handle long message IDs
- Skips processing if message already in database

## How to Verify Fix

### 1. Check Current Auto-Reply Status
```python
railway run python -c "from app import create_app, db; from app.models import ChatSettings; app = create_app(); app.app_context().push(); s = ChatSettings.query.first(); print(f'Auto-reply enabled: {s.auto_reply_enabled if s else None}')"
```

### 2. Disable Auto-Reply Temporarily
```python
railway run python -c "from app import create_app, db; from app.models import ChatSettings; app = create_app(); app.app_context().push(); s = ChatSettings.query.first(); s.auto_reply_enabled = False; db.session.commit(); print('Auto-reply disabled')"
```

### 3. Monitor API Usage
- Check Gemini API console: https://ai.google.dev/usage
- Watch Railway logs: `railway logs --tail`
- Look for: "Not replying: Auto-reply is disabled" or "Message too old"

## Prevention Tips

1. **Keep auto-reply OFF when not needed**
   - Only enable when actively monitoring
   - Disable before running tests

2. **Use the web interface to control it**
   - Go to: https://web-production-15e9.up.railway.app/settings
   - Toggle auto-reply on/off as needed

3. **Set rate limits appropriately**
   - Default: 10 replies per hour per conversation
   - Adjust in ChatSettings if needed

4. **Don't run test_webhook.py repeatedly**
   - It now skips the actual test
   - But still avoid running unless debugging

## Current Quota Status

Based on error message seen:
```
429 You exceeded your current quota
- Quota exceeded for: generate_content_free_tier_requests
- Model: gemini-2.0-flash
```

**Reset Time**: Daily (usually midnight UTC)
**Free Tier Limits**: 
- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per day

## Quick Commands

**Disable Auto-Reply**:
```powershell
railway run python -c "from app import create_app, db; from app.models import ChatSettings; app = create_app(); ctx = app.app_context(); ctx.push(); s = ChatSettings.query.first(); s.auto_reply_enabled = False if s else None; db.session.commit() if s else None; print('Disabled')"
```

**Check Recent Messages**:
```powershell
railway run python -c "from app import create_app, db; from app.models import DMMessage; from datetime import datetime, timedelta; app = create_app(); ctx = app.app_context(); ctx.push(); recent = DMMessage.query.filter(DMMessage.created_at >= datetime.utcnow() - timedelta(hours=1)).count(); print(f'Messages in last hour: {recent}')"
```

**View API Call Logs**:
```powershell
railway logs --tail | Select-String "Gemini|gemini|generate_"
```
