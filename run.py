import os
from app import create_app, db
from app.models import DMConversation

app = create_app()

# Add unread_count column if it doesn't exist (migration helper)
with app.app_context():
    try:
        # Try to add the column if it doesn't exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('dm_conversation')]
        if 'unread_count' not in columns:
            db.engine.execute('ALTER TABLE dm_conversation ADD COLUMN unread_count INTEGER DEFAULT 0')
            print("✓ Added unread_count column to dm_conversation table")
    except Exception as e:
        # Column might already exist or using different DB
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
