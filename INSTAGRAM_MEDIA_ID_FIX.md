# Instagram Publishing - Media ID Error Fix

## Problem
Error: `Instagram publish failed (HTTP 400): Media ID is not available`

## Root Cause
Instagram cannot access your image URL because:
1. ❌ PUBLIC_URL is set to localhost (Instagram can't access your local machine)
2. ❌ PUBLIC_URL is not using HTTPS (Instagram requires HTTPS)
3. ❌ PUBLIC_URL is not configured at all

## ✅ SOLUTION

### For Railway Deployment (RECOMMENDED)

1. **Get your Railway domain:**
   - Go to: https://railway.app/
   - Open your project
   - Click on your service
   - Copy the domain (e.g., `your-app.up.railway.app`)

2. **Set environment variable in Railway:**
   - Go to "Variables" tab
   - Click "New Variable"
   - Add ONE of these:
     ```
     PUBLIC_URL=https://your-app.up.railway.app
     ```
     OR
     ```
     RAILWAY_PUBLIC_DOMAIN=your-app.up.railway.app
     ```

3. **Redeploy your app:**
   - Railway will automatically redeploy
   - Or click "Deploy" → "Redeploy"

### For Local Testing with ngrok

If you're testing locally and need Instagram to work:

1. **Install ngrok:**
   - Windows: `choco install ngrok` or download from https://ngrok.com/download
   - Mac: `brew install ngrok`

2. **Run ngrok:**
   ```bash
   ngrok http 5000
   ```

3. **Copy the HTTPS URL:**
   - Look for: `Forwarding https://abc123.ngrok-free.app`
   - Copy the HTTPS URL

4. **Set in your .env file:**
   ```
   PUBLIC_URL=https://abc123.ngrok-free.app
   ```

5. **Restart your Flask app**

## Verify Configuration

Run this command to check if everything is configured correctly:

```bash
python verify_instagram_config.py
```

This will check:
- ✓ Instagram credentials are set
- ✓ PUBLIC_URL is configured
- ✓ URL uses HTTPS
- ✓ URL is not localhost
- ✓ URL is accessible
- ✓ Instagram API connection works

## What Changed in the Code

I've updated your code to:

1. **Better PUBLIC_URL detection** - Now automatically detects Railway domains from multiple environment variables
2. **Added validation** - Checks PUBLIC_URL before attempting to publish
3. **Better error messages** - Shows exactly what's wrong and how to fix it

## Testing

After setting PUBLIC_URL:

1. **Check status:**
   ```bash
   python verify_instagram_config.py
   ```

2. **Try posting:**
   - Go to your app
   - Create a new post with an image
   - Schedule or publish immediately
   - Should work! ✅

## Common Issues

### "URL is localhost"
- **Problem:** PUBLIC_URL is set to `http://127.0.0.1:5000`
- **Fix:** Set to your Railway domain or ngrok URL

### "URL does not use HTTPS"
- **Problem:** PUBLIC_URL is `http://` instead of `https://`
- **Fix:** Change to `https://your-domain.com`

### "Could not reach URL"
- **Problem:** Your Railway app is not running or domain is wrong
- **Fix:** Check Railway logs, verify domain is correct

### "Instagram API returned error"
- **Problem:** Access token expired or invalid
- **Fix:** Regenerate token from Meta Developers console

## Need Help?

Run the verification script and share the output:
```bash
python verify_instagram_config.py
```

## Quick Checklist

- [ ] PUBLIC_URL is set (Railway or ngrok)
- [ ] URL uses HTTPS
- [ ] URL is publicly accessible (not localhost)
- [ ] INSTAGRAM_ACCESS_TOKEN is set
- [ ] INSTAGRAM_BUSINESS_ACCOUNT_ID is set
- [ ] Verification script passes all checks
- [ ] Test post with image works

---

**After fixing, your posts should publish successfully! 🎉**
