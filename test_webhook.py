"""
Webhook Debugging Script
Run this locally to test webhook functionality and diagnose issues
"""
import os
import sys
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

def test_webhook_configuration():
    """Test 1: Check if all required environment variables are set"""
    print("\n" + "="*60)
    print("TEST 1: Environment Variables Check")
    print("="*60)
    
    required_vars = {
        'WEBHOOK_VERIFY_TOKEN': os.getenv('WEBHOOK_VERIFY_TOKEN'),
        'INSTAGRAM_APP_SECRET': os.getenv('INSTAGRAM_APP_SECRET'),
        'INSTAGRAM_ACCESS_TOKEN': os.getenv('INSTAGRAM_ACCESS_TOKEN'),
        'INSTAGRAM_BUSINESS_ACCOUNT_ID': os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID'),
    }
    
    all_set = True
    for var, value in required_vars.items():
        status = "✓ SET" if value else "✗ MISSING"
        print(f"{var}: {status}")
        if not value:
            all_set = False
            print(f"  ⚠ This is required for webhooks to work!")
    
    if all_set:
        print("\n✓ All required environment variables are configured")
    else:
        print("\n✗ Some required environment variables are missing")
        print("  Set them in Railway or your .env file")
    
    return all_set

def test_database_models():
    """Test 2: Check if database tables exist"""
    print("\n" + "="*60)
    print("TEST 2: Database Models Check")
    print("="*60)
    
    try:
        from app import create_app, db
        from app.models import DMConversation, DMMessage, ChatSettings
        
        app = create_app()
        with app.app_context():
            # Try to query each table
            dm_count = DMConversation.query.count()
            msg_count = DMMessage.query.count()
            settings = ChatSettings.query.first()
            
            print(f"✓ DMConversation table exists ({dm_count} records)")
            print(f"✓ DMMessage table exists ({msg_count} records)")
            print(f"✓ ChatSettings table exists")
            
            if settings:
                print(f"\nAuto-reply enabled: {settings.auto_reply_enabled}")
                print(f"Reply rate limit: {settings.reply_rate_limit}/hour")
            else:
                print("\n⚠ No ChatSettings record found - will be created on first use")
            
            return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        print("\n  Run 'flask db upgrade' or restart the app to create tables")
        return False

def test_webhook_routes():
    """Test 3: Check if webhook routes are registered"""
    print("\n" + "="*60)
    print("TEST 3: Webhook Routes Check")
    print("="*60)
    
    try:
        from app import create_app
        
        app = create_app()
        
        # Find webhook routes
        webhook_routes = []
        for rule in app.url_map.iter_rules():
            if 'webhook' in rule.rule:
                webhook_routes.append({
                    'endpoint': rule.endpoint,
                    'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                    'path': rule.rule
                })
        
        if webhook_routes:
            print("✓ Webhook routes registered:")
            for route in webhook_routes:
                print(f"  {route['methods']: <12} {route['path']}")
        else:
            print("✗ No webhook routes found")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error loading app: {e}")
        return False

def test_gemini_api():
    """Test 4: Check Gemini API configuration"""
    print("\n" + "="*60)
    print("TEST 4: Gemini AI Configuration")
    print("="*60)
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print(f"✓ GEMINI_API_KEY is set ({gemini_key[:10]}...)")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
            model = genai.GenerativeModel(model_name)
            print(f"  Using model: {model_name}")
            
            # Test generation
            response = model.generate_content("Say 'API working' if you can read this.")
            print(f"✓ Gemini API is working")
            print(f"  Test response: {response.text[:50]}...")
            return True
        except Exception as e:
            print(f"✗ Gemini API error: {e}")
            return False
    else:
        print("⚠ GEMINI_API_KEY not set")
        print("  Webhooks will still work but will use fallback messages")
        return True

def test_instagram_api():
    """Test 5: Check Instagram API access"""
    print("\n" + "="*60)
    print("TEST 5: Instagram API Access")
    print("="*60)
    
    token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    business_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if not token or not business_id:
        print("✗ Instagram credentials not set")
        return False
    
    try:
        import requests
        
        # Test API access
        url = f"https://graph.facebook.com/v19.0/me"
        params = {'access_token': token}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Instagram API access working")
            print(f"  Account ID: {data.get('id', 'N/A')}")
            return True
        else:
            print(f"✗ Instagram API error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def simulate_webhook_event():
    """Test 6: Simulate a webhook event"""
    print("\n" + "="*60)
    print("TEST 6: Simulate Webhook Event")
    print("="*60)
    
    try:
        from app import create_app
        from app.social.instagram_webhooks import handle_webhook_event
        
        app = create_app()
        
        # Sample webhook event
        test_event = {
            "object": "instagram",
            "entry": [{
                "id": "test-page-id",
                "time": int(datetime.now().timestamp()),
                "messaging": [{
                    "sender": {"id": "test-user-999"},
                    "recipient": {"id": "test-page-id"},
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "message": {
                        "mid": f"test-msg-{int(datetime.now().timestamp())}",
                        "text": "Hello, this is a test message!"
                    }
                }]
            }]
        }
        
        print("Simulating incoming message...")
        print(f"  From: test-user-999")
        print(f"  Text: {test_event['entry'][0]['messaging'][0]['message']['text']}")
        
        with app.app_context():
            result = handle_webhook_event(test_event)
            
            if result.get('success'):
                print(f"\n✓ Webhook processed successfully")
                print(f"  Processed: {result.get('processed', 0)} events")
                if result.get('results'):
                    for r in result['results']:
                        if r.get('replied'):
                            print(f"  ✓ Auto-reply sent: {r.get('reply_text', '')[:50]}...")
                        else:
                            print(f"  ℹ No reply sent: {r.get('reason', 'Unknown')}")
                return True
            else:
                print(f"\n✗ Webhook processing failed")
                print(f"  Error: {result.get('error', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"✗ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_recent_conversations():
    """Test 7: Check if any DMs were received"""
    print("\n" + "="*60)
    print("TEST 7: Recent DM Conversations")
    print("="*60)
    
    try:
        from app import create_app, db
        from app.models import DMConversation, DMMessage
        
        app = create_app()
        with app.app_context():
            conversations = DMConversation.query.order_by(DMConversation.last_message_at.desc()).limit(5).all()
            
            if conversations:
                print(f"✓ Found {len(conversations)} recent conversations:")
                for conv in conversations:
                    print(f"\n  User: {conv.instagram_username or conv.instagram_user_id}")
                    print(f"  Messages: {conv.message_count} (Auto-replies: {conv.auto_reply_count})")
                    print(f"  Last message: {conv.last_message_at}")
                    print(f"  Status: {conv.conversation_status}")
                    
                    # Show last message
                    last_msg = conv.messages.order_by(DMMessage.created_at.desc()).first()
                    if last_msg:
                        print(f"  Last: [{last_msg.sender_type}] {last_msg.message_text[:50]}...")
                return True
            else:
                print("ℹ No DM conversations found in database")
                print("\n  This means:")
                print("  1. No webhook events have been received yet")
                print("  2. Or webhook events are failing to process")
                print("  3. Or Instagram hasn't sent any DMs to the webhook")
                return False
    except Exception as e:
        print(f"✗ Database query error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("INSTAGRAM WEBHOOK DIAGNOSTIC TOOL")
    print("="*60)
    
    results = {
        'Environment Variables': test_webhook_configuration(),
        'Database Models': test_database_models(),
        'Webhook Routes': test_webhook_routes(),
        'Gemini AI': test_gemini_api(),
        'Instagram API': test_instagram_api(),
        'Simulation Test': simulate_webhook_event(),
        'Recent DMs': check_recent_conversations(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status: <10} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Your webhook should be working.")
        print("\nIf you're still not seeing DMs:")
        print("  1. Check Instagram App Dashboard webhook subscriptions")
        print("  2. Verify the callback URL is correct")
        print("  3. Check Railway logs for incoming webhook requests")
        print("  4. Send a test message from a different Instagram account")
    else:
        print("\n✗ Some tests failed. Fix the issues above and try again.")
    
    print("\nTo check Railway logs:")
    print("  railway logs --tail")

if __name__ == '__main__':
    main()
