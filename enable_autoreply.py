"""
Quick Fix Script - Enable Auto-Reply and Check Configuration
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

def quick_fix():
    """Enable auto-reply and check basic configuration"""
    from app import create_app, db
    from app.models import ChatSettings
    
    app = create_app()
    
    with app.app_context():
        # Get or create ChatSettings
        settings = ChatSettings.query.first()
        
        if not settings:
            print("Creating ChatSettings record...")
            settings = ChatSettings(
                auto_reply_enabled=True,  # Enable by default
                auto_comment_enabled=False,
                reply_rate_limit=10,
                comment_rate_limit=20,
                business_hours_only=False,
                business_hours_start="09:00",
                business_hours_end="18:00",
                default_greeting="Hello! Thanks for reaching out. How can I help you today?",
                fallback_message="I'm sorry, I didn't quite understand that. Could you please rephrase?"
            )
            db.session.add(settings)
            db.session.commit()
            print("✓ ChatSettings created with auto-reply ENABLED")
        else:
            print(f"Current auto-reply status: {'ENABLED' if settings.auto_reply_enabled else 'DISABLED'}")
            
            if not settings.auto_reply_enabled:
                settings.auto_reply_enabled = True
                db.session.commit()
                print("✓ Auto-reply has been ENABLED")
            else:
                print("✓ Auto-reply is already enabled")
        
        print(f"\nCurrent settings:")
        print(f"  Auto-reply: {settings.auto_reply_enabled}")
        print(f"  Rate limit: {settings.reply_rate_limit}/hour")
        print(f"  Business hours only: {settings.business_hours_only}")
        print(f"  Default greeting: {settings.default_greeting[:50]}...")
        print(f"  Fallback message: {settings.fallback_message[:50]}...")

if __name__ == '__main__':
    quick_fix()
