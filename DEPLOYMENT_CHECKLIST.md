# ✅ Railway Deployment Checklist

## Pre-Deployment Steps (Local)

### 1. Code Changes ✅ COMPLETE
- [x] run.py updated with automation table creation
- [x] automation_handlers.py: Instagram API implemented
- [x] All automation files created and integrated
- [x] No syntax errors in any files

### 2. Review Changes
```powershell
# Check what files changed
git status

# Review your changes
git diff
```

Expected changes:
- ✅ `run.py` - Table creation logic added
- ✅ `app/automation_handlers.py` - Instagram API implemented
- ✅ `app/models.py` - 4 new models
- ✅ `app/automation_routes.py` - New routes file
- ✅ `app/templates/automation/` - 4 new templates
- ✅ `app/templates/base.html` - Navigation updated
- ✅ `app/social/instagram_webhooks.py` - Comment routing
- ✅ `app/__init__.py` - Blueprint registration

---

## Deployment to Railway

### Step 1: Commit and Push

```powershell
# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add Automations Suite: auto-comment replies and comment-to-DM triggers"

# Push to repository (Railway will auto-deploy)
git push origin main
```

**Alternative using Railway CLI:**
```powershell
railway login
railway link
railway up
```

### Step 2: Monitor Deployment

Watch deployment logs:
```powershell
railway logs --follow
```

**Look for these success messages:**
```
✓ Added unread_count column to dm_conversation table
✓ Created auto_reply_settings table
✓ Created comment_trigger table
✓ Created comment_dm_tracker table
✓ Created automation_log table
✅ All automation tables ready
```

---

## Post-Deployment Configuration

### Step 3: Verify Environment Variables

In Railway Dashboard → Your Project → Variables:

#### Required Variables (should already exist):
- `DATABASE_URL` - Auto-configured by Railway
- `SECRET_KEY` - Your Flask secret key
- `INSTAGRAM_ACCESS_TOKEN` - Your Instagram token
- `INSTAGRAM_BUSINESS_ACCOUNT_ID` - Your Instagram account ID

#### Verify Instagram Token Permissions:
Your token must have these scopes:
- ✅ `instagram_basic`
- ✅ `instagram_manage_messages`
- ✅ `instagram_manage_comments` ← **CRITICAL for auto-replies**
- ✅ `pages_read_engagement`

**If missing `instagram_manage_comments`:**
1. Go to [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Add `instagram_manage_comments` permission
4. Generate new token
5. Update `INSTAGRAM_ACCESS_TOKEN` in Railway

### Step 4: Configure Instagram Webhooks

1. Go to [Meta for Developers](https://developers.facebook.com/apps/)
2. Select your app
3. Navigate to **Webhooks** → **Instagram**
4. Click **Edit Subscription**
5. **Enable the `comments` field** ✅
6. Verify callback URL: `https://your-app.railway.app/webhook/instagram`
7. Save changes

**Test webhook delivery:**
- Post a comment on your Instagram
- Check Railway logs for webhook event

---

## Testing & Verification

### Step 5: Access Automations Dashboard

Visit:
```
https://your-app.railway.app/automations
```

You should see 3 cards:
- 💬 DM Automation
- 💬 Auto-Comment Replies
- 📨 Comment-to-DM

### Step 6: Configure Auto-Comment Replies

1. Click **💬 Auto-Comment Replies**
2. Enable for Instagram ✅
3. Configure:
   - Enable RAG: ✅
   - Fallback message: "Thanks for your comment! 🙏"
   - Tone: Friendly
   - Response delay: 5 seconds
   - Rate limit: 20 per hour
4. Save Settings

### Step 7: Create Comment-to-DM Trigger

1. Click **📨 Comment-to-DM**
2. Add trigger:
   - Keyword: `DM ME`
   - Message: `Check your DMs for something special! 🎁`
   - Enable RAG: Optional
   - Active: ✅
3. Click Add Trigger

### Step 8: Test Live

#### Test Auto-Comment:
1. Post a comment on your Instagram post
2. Wait 5-10 seconds
3. ✅ Check if auto-reply appears on Instagram
4. ✅ Verify in logs: `https://your-app.railway.app/automations/logs`

#### Test Comment-to-DM:
1. Comment "DM ME" on your Instagram post
2. ✅ Check your Instagram DMs for automated message
3. ✅ Verify in logs: `https://your-app.railway.app/automations/logs`

---

## Troubleshooting

### Tables Not Created?

**Check Railway logs:**
```powershell
railway logs | Select-String "automation tables"
```

**Manual fix via Railway shell:**
```powershell
railway shell
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Webhooks Not Triggering?

**Check Railway logs:**
```powershell
railway logs | Select-String "webhook"
```

**Verify webhook in Meta Dashboard:**
- Callback URL is correct
- SSL certificate is valid
- `comments` field is enabled
- Test delivery succeeds

**Test webhook manually:**
```powershell
# Using curl or Invoke-WebRequest
$url = "https://your-app.railway.app/webhook/instagram"
Invoke-WebRequest -Uri $url -Method GET
```

### Auto-Reply Not Posting?

**Check logs for errors:**
```powershell
railway logs | Select-String "comment reply"
```

**Common issues:**
- Access token missing `instagram_manage_comments`
- Token expired - regenerate in Meta dashboard
- Comment ID format incorrect
- Instagram API rate limits

### RAG Not Working?

**Check RAG status:**
```
https://your-app.railway.app/rag/status
```

**Verify:**
- Gemini API key configured
- RAG has ingested content
- Fallback messages are set

---

## Success Indicators

### ✅ Deployment Successful When:

1. **Logs show:**
   ```
   ✅ All automation tables ready
   Gunicorn running on port $PORT
   No Python errors
   ```

2. **Dashboard accessible:**
   - Can access /automations
   - All 3 cards visible
   - No 500 errors

3. **Settings pages work:**
   - /automations/auto-comment loads
   - /automations/comment-to-dm loads
   - Can save settings without errors

4. **Webhooks processing:**
   - Instagram comments trigger webhooks
   - Logs show "Processing comment automation"
   - Auto-replies post successfully

5. **Automations working:**
   - Auto-comment replies appear on Instagram
   - DMs sent for trigger keywords
   - Activity logged at /automations/logs

---

## Quick Commands

```powershell
# Deploy
git push origin main

# View logs
railway logs

# Real-time logs
railway logs --follow

# Restart app
railway restart

# Open in browser
railway open

# Check status
railway status

# Environment variables
railway variables

# Shell access
railway shell
```

---

## Final Checklist

### Before Going Live:
- [ ] All code pushed to Git repository
- [ ] Railway deployment successful
- [ ] Tables created (verified in logs)
- [ ] Environment variables configured
- [ ] Instagram token has `instagram_manage_comments`
- [ ] Webhooks configured for `comments` field
- [ ] Accessed /automations dashboard successfully
- [ ] Auto-comment settings configured
- [ ] At least one comment-to-DM trigger created
- [ ] Tested with real Instagram comment
- [ ] Auto-reply appeared on Instagram
- [ ] DM automation worked
- [ ] Activity logged correctly
- [ ] No errors in Railway logs

### Monitoring First 24 Hours:
- [ ] Check Railway logs hourly
- [ ] Monitor automation success rate
- [ ] Verify no API rate limit errors
- [ ] Adjust rate limits if needed
- [ ] Review RAG response quality
- [ ] Test edge cases (long comments, emojis, etc.)

---

## 🎉 You're Live!

Once all checkboxes are ✅, your Automations Suite is fully operational on Railway!

**Next Steps:**
- Monitor automation logs daily
- Optimize RAG responses based on user feedback
- Create additional comment-to-DM triggers
- Adjust rate limits based on usage
- Review analytics weekly

**Happy Automating! 🚂💨**

---

## Support

Need help? Check:
- [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - Complete guide
- [AUTOMATIONS_SUITE_GUIDE.md](AUTOMATIONS_SUITE_GUIDE.md) - Feature details
- Railway logs: `railway logs`
- Instagram API docs: https://developers.facebook.com/docs/instagram-api
