import os
from app import create_app, db
from app.models import DMConversation

app = create_app()

# Add unread_count column if it doesn't exist (migration helper for MySQL/PostgreSQL)
with app.app_context():
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('dm_conversation')]
        if 'unread_count' not in columns:
            # MySQL uses INT, PostgreSQL uses INTEGER - both work with this
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE dm_conversation ADD COLUMN unread_count INT DEFAULT 0'))
                conn.commit()
            print("✓ Added unread_count column to dm_conversation table")
    except Exception as e:
        # Column might already exist or permissions issue
        print(f"Note: Could not add unread_count column (it may already exist): {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
