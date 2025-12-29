"""
Disable Auto-Reply to Stop Gemini API Calls
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import ChatSettings

app = create_app()

with app.app_context():
    settings = ChatSettings.query.first()
    
    if settings:
        print(f"Current auto-reply status: {settings.auto_reply_enabled}")
        settings.auto_reply_enabled = False
        db.session.commit()
        print("✓ Auto-reply has been DISABLED")
        print("  This will prevent further Gemini API calls")
    else:
        print("No ChatSettings found in database")
