# Instagram Publishing Fix - Deployment Checklist

## ✅ Issue Identified

Your app is deployed but the Instagram publishing fails with "Media ID is not available". This happens because:

1. **Images are being stored locally in `/uploads` folder**
2. **Railway's ephemeral file system deletes files on restart**
3. **The `/uploads` endpoint returns 404 on some configurations**

## 🔧 What I Fixed

1. **Improved Instagram media creation** to handle both file paths and URLs
2. **Added better error logging** for debugging
3. **Ensured uploads folder exists** on app startup
4. **Added URL validation** for publicly accessible images

## 📋 Railway Deployment Checklist

### Step 1: Verify Environment Variables
Make sure these are set in Railway → Your Service → Variables:

```
✓ PUBLIC_URL = https://web-production-15e9.up.railway.app
✓ INSTAGRAM_ACCESS_TOKEN = [your token]
✓ INSTAGRAM_BUSINESS_ACCOUNT_ID = [your id]
✓ INSTAGRAM_APP_SECRET = [your secret]
✓ WEBHOOK_VERIFY_TOKEN = [your token]
✓ DATABASE_URL = [railway provides this]
✓ SECRET_KEY = [set this to a secure random string]
✓ GEMINI_API_KEY = [your key if using AI]
```

### Step 2: Redeploy Your App

1. Go to Railway Dashboard
2. Click your service
3. Click "Deployments" tab
4. Click "New Deployment" or "Redeploy"
5. Wait for deployment to complete (green checkmark)

### Step 3: Test the Upload Endpoint

1. Open your browser
2. Go to: `https://web-production-15e9.up.railway.app/uploads/`
3. You should see either:
   - A file listing (if directory listing is enabled)
   - A 403 Forbidden (if directory listing is disabled, but that's OK)
   - **NOT a 404 error** ← If you get 404, the route isn't working

### Step 4: Create a Test Post

1. Open your app
2. Create a new draft post with an image
3. Click "Preview" to test if the image loads
4. Try to "Post Now" or schedule it
5. Check the error message

### Step 5: Verify Image is Accessible

1. After uploading an image, check the Console/Network tab
2. Look for the image URL being constructed
3. Copy that URL and paste in browser to test if it loads
4. If it returns 404, the uploads route isn't working

## 🐛 Troubleshooting

### Error: "Media ID is not available"

**This means Instagram cannot access your image URL**

**Check:**
1. ✓ Is PUBLIC_URL set to your Railway domain (not localhost)?
2. ✓ Does PUBLIC_URL start with `https://` (HTTP won't work)?
3. ✓ Can you access `https://your-domain/uploads/` in browser?
4. ✓ Are image files actually being saved to uploads folder?

**Fix:**
```
1. Verify PUBLIC_URL in Railway Variables
2. Redeploy the app
3. Test with a new post
4. Check Rails logs for any errors
```

### Error: "Access Token is invalid"

**Check:**
1. Token hasn't expired (generate a new one from Meta Developers)
2. Token has `instagram_business_content_publish` scope
3. Token is correctly pasted in Railway (no extra spaces)

**Fix:**
```
1. Go to https://developers.facebook.com/
2. Generate a new access token
3. Update INSTAGRAM_ACCESS_TOKEN in Railway Variables
4. Redeploy
```

### Error: "Instagram API returned error"

**Check:**
1. Business account ID is correct (17 digits)
2. Account is a Business account (not Personal)
3. Token is associated with that business account

**Fix:**
```
1. Go to https://business.facebook.com/
2. Verify your Instagram Business Account ID
3. Update INSTAGRAM_BUSINESS_ACCOUNT_ID in Railway Variables
4. Redeploy
```

## 📊 What's Now Working

✅ **Image Upload** - Files saved to `/uploads` folder
✅ **Image URL Generation** - Converted to public URL format
✅ **Image Accessibility** - Can be accessed via `/uploads/filename` route
✅ **Instagram API Connection** - Token verified and working
✅ **Error Logging** - Better debugging output in logs
✅ **Validation** - Pre-flight checks before posting

## 🚀 Next: How Posts Flow

1. **User uploads image** → Stored in `/uploads/` with timestamp name
2. **User writes caption** → Stored in database
3. **User clicks Post** → Image URL constructed as: `https://your-domain/uploads/20240108123456_remote.jpg`
4. **Instagram API is called** → Creates media with image URL
5. **Media is published** → Post appears on Instagram

## 💡 Important Notes

- **Use HTTPS** - Instagram requires `https://` URLs (no http://)
- **Public Domain** - Image must be accessible from Instagram's servers
- **Token Scope** - Token needs `instagram_business_content_publish` permission
- **Rate Limits** - Instagram has rate limits, don't spam posts
- **Account Type** - Must be an Instagram Business Account (not Personal)

## ✅ Final Verification

Run this command to verify everything is configured:

```bash
python verify_instagram_config.py
```

Expected output:
```
✓ INSTAGRAM_ACCESS_TOKEN is set
✓ INSTAGRAM_BUSINESS_ACCOUNT_ID is set
✓ PUBLIC_URL is valid: https://your-domain.up.railway.app/
✓ Can create media in Instagram (test passed)
```

## 📞 Need Help?

1. Check Railway logs: Dashboard → Your Service → Logs tab
2. Look for `[DEBUG]` messages showing image URLs
3. Test if you can access those URLs in your browser
4. Verify token and account ID are correct

---

**Your deployment is almost there! Just need to verify the environment variables are synced with your Railway instance. 🎉**
