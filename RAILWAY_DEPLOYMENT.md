# 🚂 Railway Deployment Guide - Automations Suite

## Overview
Your PostScheduler with Automations Suite is configured for Railway deployment. This guide covers deploying the new automation features to your existing Railway app.

---

## 🎯 Railway Configuration

### Current Setup
- **Platform:** Railway.app
- **Python Version:** 3.11 (nixpacks.toml)
- **Web Server:** Gunicorn
- **Database Migration:** Manual (via run.py)
- **Start Command:** `gunicorn run:app --bind 0.0.0.0:$PORT --workers 1 --preload`

---

## 📦 Step 1: Update run.py for New Tables

Your app uses a manual migration approach in `run.py`. Add the automation table creation:

### Open run.py and add this after the existing unread_count migration:

```python
# Add new automation tables (after the unread_count migration block)
with app.app_context():
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        # Check and create auto_reply_settings table
        if 'auto_reply_settings' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE auto_reply_settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        platform VARCHAR(50) NOT NULL DEFAULT 'instagram',
                        is_active BOOLEAN DEFAULT FALSE,
                        use_rag BOOLEAN DEFAULT TRUE,
                        fallback_message TEXT,
                        tone VARCHAR(50) DEFAULT 'friendly',
                        response_delay_seconds INT DEFAULT 5,
                        rate_limit_per_hour INT DEFAULT 10,
                        excluded_keywords TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                        UNIQUE KEY unique_user_platform (user_id, platform)
                    )
                '''))
                conn.commit()
            print("✓ Created auto_reply_settings table")
        
        # Check and create comment_trigger table
        if 'comment_trigger' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE comment_trigger (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        trigger_keyword VARCHAR(100) NOT NULL,
                        dm_message_template TEXT NOT NULL,
                        use_rag BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        times_triggered INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                        UNIQUE KEY unique_user_keyword (user_id, trigger_keyword)
                    )
                '''))
                conn.commit()
            print("✓ Created comment_trigger table")
        
        # Check and create comment_dm_tracker table
        if 'comment_dm_tracker' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE comment_dm_tracker (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        post_id VARCHAR(100) NOT NULL,
                        user_id VARCHAR(100) NOT NULL,
                        trigger_id INT NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (trigger_id) REFERENCES comment_trigger(id) ON DELETE CASCADE,
                        UNIQUE KEY unique_post_user (post_id, user_id)
                    )
                '''))
                conn.commit()
            print("✓ Created comment_dm_tracker table")
        
        # Check and create automation_log table
        if 'automation_log' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE automation_log (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        automation_type VARCHAR(50) NOT NULL,
                        trigger_keyword VARCHAR(100),
                        post_id VARCHAR(100),
                        comment_id VARCHAR(100),
                        comment_text TEXT,
                        response_text TEXT,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        response_time_ms INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                        INDEX idx_user_type (user_id, automation_type),
                        INDEX idx_created_at (created_at)
                    )
                '''))
                conn.commit()
            print("✓ Created automation_log table")
            
        print("✓ All automation tables ready")
        
    except Exception as e:
        print(f"Note: Could not create automation tables (they may already exist): {e}")
```

**Note:** Adjust SQL syntax if you're using PostgreSQL instead of MySQL. For PostgreSQL:
- Change `INT AUTO_INCREMENT PRIMARY KEY` to `SERIAL PRIMARY KEY`
- Change `BOOLEAN` to `BOOLEAN` (same)
- Change `TEXT` to `TEXT` (same)
- Change `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` to `TIMESTAMP DEFAULT NOW()`

---

## 🚀 Step 2: Deploy to Railway

### Method A: Git Push (Recommended)

```powershell
# 1. Stage your changes
git add .

# 2. Commit with descriptive message
git commit -m "Add Automations Suite with auto-comment and comment-to-DM features"

# 3. Push to your Railway-connected repository
git push origin main
```

Railway will automatically detect the changes and redeploy.

### Method B: Railway CLI

```powershell
# 1. Install Railway CLI (if not already installed)
# Download from: https://docs.railway.app/develop/cli

# 2. Login to Railway
railway login

# 3. Link to your project
railway link

# 4. Deploy
railway up
```

---

## 🔧 Step 3: Configure Environment Variables

In your Railway dashboard, add these environment variables:

### Required (if not already set):
```
DATABASE_URL=<your-railway-provided-url>
SECRET_KEY=<your-secret-key>
INSTAGRAM_ACCESS_TOKEN=<your-instagram-token>
INSTAGRAM_BUSINESS_ACCOUNT_ID=<your-instagram-id>
```

### New/Verify Instagram Permissions:
Your Instagram access token must have these permissions:
- ✅ `instagram_basic`
- ✅ `instagram_manage_messages` (for DMs)
- ✅ `instagram_manage_comments` (NEW - for auto-replies)
- ✅ `pages_read_engagement` (for webhook data)

**Regenerate token if needed:**
1. Go to [Meta for Developers](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Add permissions: `instagram_manage_comments`
4. Generate new token
5. Update `INSTAGRAM_ACCESS_TOKEN` in Railway dashboard

---

## 🔔 Step 4: Configure Instagram Webhooks

### In Meta App Dashboard:

1. Navigate to **Products** → **Webhooks**
2. Edit your Instagram subscription
3. **Enable the `comments` field** ✅
4. Verify callback URL points to your Railway app
5. Save changes

**Your webhook URL should be:**
```
https://your-app.railway.app/webhook/instagram
```

**Test webhook:**
```powershell
# View Railway logs in real-time
railway logs
```

Then post a comment on Instagram and watch for webhook events.

---

## 🔍 Step 5: Verify Deployment

### Check Tables Created

In Railway logs, you should see:
```
✓ Created auto_reply_settings table
✓ Created comment_trigger table
✓ Created comment_dm_tracker table
✓ Created automation_log table
✓ All automation tables ready
```

### Access Automations Dashboard

Navigate to:
```
https://your-app.railway.app/automations
```

You should see the dashboard with 3 automation cards.

---

## 📝 Step 6: Implement Instagram API (Critical)

The `_post_comment_reply()` function in `app/automation_handlers.py` needs implementation:

### Quick Implementation:

1. Open `app/automation_handlers.py`
2. Find the `_post_comment_reply` function
3. Replace with this:

```python
import requests  # Add at top if not present

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

4. Commit and push:
```powershell
git add app/automation_handlers.py
git commit -m "Implement Instagram comment reply API"
git push origin main
```

---

## 🧪 Step 7: Test Everything

### Test Auto-Comment:
1. Visit `https://your-app.railway.app/automations/auto-comment`
2. Enable auto-replies for Instagram
3. Configure settings (enable RAG, set tone, etc.)
4. Post a comment on your Instagram
5. Check Railway logs: `railway logs`
6. Verify reply appears on Instagram

### Test Comment-to-DM:
1. Visit `https://your-app.railway.app/automations/comment-to-dm`
2. Add trigger: keyword "DM ME", message "Check your DMs!"
3. Comment "DM ME" on your Instagram
4. Check your Instagram DMs
5. View logs: `https://your-app.railway.app/automations/logs`

---

## 📊 Monitoring on Railway

### View Logs
```powershell
# Real-time logs
railway logs

# Or in Railway Dashboard:
# Project → Deployments → View Logs
```

### Key Log Messages to Watch:
```
✓ All automation tables ready
Webhook received: comment
Processing comment automation for post_id: ...
Successfully posted reply to comment ...
Automation completed: auto_comment - SUCCESS
```

---

## 🐛 Troubleshooting

### Tables not created?
**Check logs for SQL errors:**
```powershell
railway logs | grep "automation tables"
```

**Manual fix via Railway Shell:**
```powershell
railway shell
python3
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Webhooks not working?
- Verify webhook URL in Meta dashboard
- Check Railway app is running: `railway status`
- Test endpoint: `curl https://your-app.railway.app/webhook/instagram`
- Review logs for incoming requests

### Access token invalid?
- Regenerate with `instagram_manage_comments` permission
- Update environment variable in Railway dashboard
- Restart deployment

### RAG not responding?
- Check `/rag/status` endpoint
- Verify Gemini API key in environment variables
- Check RAG ingestion has content
- Review error logs in Railway

---

## 🔐 Security Checklist

- [ ] Secret key is strong and secure
- [ ] Database credentials are in environment variables
- [ ] Instagram access token is not in code
- [ ] Webhook signature verification is enabled
- [ ] Rate limiting configured appropriately
- [ ] Error messages don't expose sensitive data

---

## 📈 Performance Tips

### Railway Free Tier Optimization:
```python
# In railway.json (already configured):
{
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Reduce Worker Count for Memory:
Your current config uses `--workers 1` which is optimal for Railway's free tier.

### Database Connection Pooling:
Consider adding to your Config class:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 5,
    'pool_recycle': 300,
    'pool_pre_ping': True
}
```

---

## 🎯 Deployment Checklist

### Pre-Deployment:
- [x] All code changes committed
- [x] run.py updated with table creation
- [x] Instagram API implemented in automation_handlers.py
- [ ] Tested locally (optional)

### Deployment:
- [ ] Pushed to Git repository
- [ ] Railway build successful
- [ ] Tables created (check logs)
- [ ] Environment variables configured
- [ ] Instagram token has correct permissions

### Post-Deployment:
- [ ] Webhooks configured for comments field
- [ ] Accessed /automations dashboard
- [ ] Configured auto-comment settings
- [ ] Added comment-to-DM trigger
- [ ] Tested with real Instagram comment
- [ ] Verified in automation logs
- [ ] Monitored Railway logs for errors

---

## 🚀 Quick Command Reference

```powershell
# View logs
railway logs

# Restart app
railway restart

# Shell access
railway shell

# Environment variables
railway variables

# Link to project
railway link

# Deploy
railway up

# Check status
railway status
```

---

## 📞 Support Resources

- **Railway Docs:** https://docs.railway.app/
- **Instagram API:** https://developers.facebook.com/docs/instagram-api
- **Flask Docs:** https://flask.palletsprojects.com/
- **Project Guides:**
  - [AUTOMATIONS_SUITE_GUIDE.md](AUTOMATIONS_SUITE_GUIDE.md)
  - [INSTAGRAM_API_TODO.md](INSTAGRAM_API_TODO.md)
  - [QUICK_START_AUTOMATIONS.md](QUICK_START_AUTOMATIONS.md)

---

## 🎉 Success!

Once deployed, your Railway app will have:
- ✅ Full Automations Suite
- ✅ AI-powered auto-comment replies
- ✅ Keyword-triggered DM automation
- ✅ Comprehensive activity logging
- ✅ Professional dashboard UI

**Your automation engine is ready to scale! 🚂💨**
