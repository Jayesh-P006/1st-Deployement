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

# Add automation tables for Automations Suite
with app.app_context():
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        # Check and create auto_reply_settings table
        if 'auto_reply_settings' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                # Note: Adjust syntax if using PostgreSQL (use SERIAL instead of AUTO_INCREMENT, etc.)
                conn.execute(text('''
                    CREATE TABLE auto_reply_settings (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        user_id INTEGER NOT NULL,
                        platform VARCHAR(50) NOT NULL DEFAULT 'instagram',
                        is_active BOOLEAN DEFAULT 0,
                        use_rag BOOLEAN DEFAULT 1,
                        fallback_message TEXT,
                        tone VARCHAR(50) DEFAULT 'friendly',
                        response_delay_seconds INTEGER DEFAULT 5,
                        rate_limit_per_hour INTEGER DEFAULT 10,
                        excluded_keywords TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                        UNIQUE (user_id, platform)
                    )
                '''))
                conn.commit()
            print("✓ Created auto_reply_settings table")
        
        # Check and create comment_trigger table
        if 'comment_trigger' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE comment_trigger (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        user_id INTEGER NOT NULL,
                        trigger_keyword VARCHAR(100) NOT NULL,
                        dm_message_template TEXT NOT NULL,
                        use_rag BOOLEAN DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        times_triggered INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                        UNIQUE (user_id, trigger_keyword)
                    )
                '''))
                conn.commit()
            print("✓ Created comment_trigger table")
        
        # Check and create comment_dm_tracker table
        if 'comment_dm_tracker' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE comment_dm_tracker (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        post_id VARCHAR(100) NOT NULL,
                        user_id VARCHAR(100) NOT NULL,
                        trigger_id INTEGER NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (trigger_id) REFERENCES comment_trigger(id) ON DELETE CASCADE,
                        UNIQUE (post_id, user_id)
                    )
                '''))
                conn.commit()
            print("✓ Created comment_dm_tracker table")
        
        # Check and create automation_log table
        if 'automation_log' not in inspector.get_table_names():
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE automation_log (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        user_id INTEGER NOT NULL,
                        automation_type VARCHAR(50) NOT NULL,
                        trigger_keyword VARCHAR(100),
                        post_id VARCHAR(100),
                        comment_id VARCHAR(100),
                        comment_text TEXT,
                        response_text TEXT,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT,
                        response_time_ms INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                    )
                '''))
                conn.commit()
            print("✓ Created automation_log table")
            
        print("✅ All automation tables ready")
        
    except Exception as e:
        print(f"Note: Could not create automation tables (they may already exist): {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
