# 🚂 Railway Deployment - Quick Reference

## Deploy Now (3 Commands)

```powershell
# 1. Commit your changes
git add .
git commit -m "Add Automations Suite"

# 2. Push to Railway
git push origin main

# 3. Watch deployment
railway logs --follow
```

**✅ Look for:** "All automation tables ready" in logs

---

## Post-Deploy Setup (5 Minutes)

### 1. Check Instagram Token Permissions
**Required:** `instagram_manage_comments` permission

**Update token if needed:**
- Go to: https://developers.facebook.com/tools/explorer/
- Add `instagram_manage_comments` permission
- Generate new token
- Update in Railway Dashboard → Variables → `INSTAGRAM_ACCESS_TOKEN`

### 2. Enable Comment Webhooks
- Go to: https://developers.facebook.com/apps/
- Select your app → Webhooks → Instagram
- ✅ Enable `comments` field
- Save

### 3. Test the Setup
1. Visit: `https://your-app.railway.app/automations`
2. Configure auto-comment settings
3. Add a comment-to-DM trigger
4. Post a test comment on Instagram
5. Verify automation works

---

## Essential Railway Commands

```powershell
# View logs
railway logs

# Real-time monitoring
railway logs --follow

# Restart app
railway restart

# Open in browser
railway open

# Check environment variables
railway variables

# Shell access
railway shell

# Deployment status
railway status
```

---

## Key Files Modified

| File | Change |
|------|--------|
| `run.py` | ✅ Added automation table creation |
| `app/automation_handlers.py` | ✅ Implemented Instagram API |
| `app/models.py` | ✅ Added 4 automation models |
| `app/automation_routes.py` | ✅ New routes blueprint |
| `app/templates/base.html` | ✅ Navigation updated |
| `app/social/instagram_webhooks.py` | ✅ Comment event routing |

---

## What Tables Get Created?

When you deploy, Railway will create:

1. **auto_reply_settings** - Comment reply configuration
2. **comment_trigger** - Keyword-based DM triggers
3. **comment_dm_tracker** - Duplicate prevention
4. **automation_log** - Activity logging

---

## Success Indicators

### ✅ Deployment worked if:
- Railway build completes without errors
- Logs show "All automation tables ready"
- Can access `/automations` dashboard
- Settings pages load without errors

### ✅ Automations working if:
- Instagram comments trigger webhooks (check logs)
- Auto-replies appear on Instagram posts
- DMs sent for trigger keywords
- Activity shows in `/automations/logs`

---

## Troubleshooting

### No tables created?
```powershell
railway shell
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Webhooks not working?
- Check callback URL in Meta dashboard
- Verify `comments` field enabled
- Test: `railway logs | Select-String "webhook"`

### Auto-replies not posting?
- Check token has `instagram_manage_comments`
- Verify token not expired
- Review: `railway logs | Select-String "comment reply"`

---

## URLs You'll Need

| Purpose | URL |
|---------|-----|
| Your App | `https://your-app.railway.app` |
| Automations Dashboard | `https://your-app.railway.app/automations` |
| Activity Logs | `https://your-app.railway.app/automations/logs` |
| Railway Dashboard | https://railway.app/dashboard |
| Meta Developer Console | https://developers.facebook.com/apps/ |
| Instagram Graph Explorer | https://developers.facebook.com/tools/explorer/ |

---

## Environment Variables Required

```
DATABASE_URL            ← Auto-configured by Railway
SECRET_KEY              ← Your Flask secret
INSTAGRAM_ACCESS_TOKEN  ← With instagram_manage_comments
INSTAGRAM_BUSINESS_ACCOUNT_ID
GEMINI_API_KEY          ← For RAG (if using)
```

---

## Testing Workflow

1. **Deploy:**
   ```powershell
   git push origin main
   railway logs --follow
   ```

2. **Configure:**
   - Visit `/automations/auto-comment`
   - Enable auto-replies
   - Add comment-to-DM trigger

3. **Test:**
   - Comment on your Instagram post
   - Wait 5-10 seconds
   - Check for auto-reply on Instagram
   - Verify in `/automations/logs`

4. **Monitor:**
   ```powershell
   railway logs | Select-String "automation"
   ```

---

## Need Help?

**Detailed Guides:**
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Step-by-step
- [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - Complete Railway guide
- [AUTOMATIONS_SUITE_GUIDE.md](AUTOMATIONS_SUITE_GUIDE.md) - Feature documentation

**Quick Debug:**
```powershell
# Check if app is running
railway status

# View recent errors
railway logs | Select-String "error" -CaseSensitive

# Restart if needed
railway restart
```

---

## 🎯 Your Next Steps

1. [ ] Run `git push origin main`
2. [ ] Watch deployment in Railway logs
3. [ ] Verify tables created successfully
4. [ ] Check Instagram token permissions
5. [ ] Enable comment webhooks in Meta
6. [ ] Configure automation settings
7. [ ] Test with real Instagram comment
8. [ ] Monitor logs for 24 hours

**Estimated time:** 10-15 minutes

---

**🚀 Ready to deploy? Just push to git and Railway handles the rest!**
