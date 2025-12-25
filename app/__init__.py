from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

from config import Config

db = SQLAlchemy()
scheduler = BackgroundScheduler()

# Import placed below to avoid circular import
# (posting logic will be loaded after db defined)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    
    # Add custom Jinja filter for JSON parsing
    import json
    @app.template_filter('from_json')
    def from_json_filter(s):
        try:
            return json.loads(s)
        except:
            return []

    if not scheduler.running:
        scheduler.start()

    from .models import ScheduledPost, TokenUsage
    from .social.instagram import post_to_instagram
    from .social.linkedin import post_to_linkedin

    def execute_post(post_id):
        with app.app_context():
            post = ScheduledPost.query.get(post_id)
            if not post or post.status != 'scheduled':
                return
            try:
                token_used = 0
                if post.platform == 'instagram':
                    token_used = post_to_instagram(post)
                elif post.platform == 'linkedin':
                    token_used = post_to_linkedin(post)
                post.status = 'posted'
                post.token_used = token_used
                
                # Update token usage
                usage = TokenUsage.query.filter_by(platform=post.platform).first()
                if usage:
                    usage.used_today += token_used
            except Exception as e:
                post.status = 'failed'
                post.error_message = str(e)[:500]
            db.session.commit()

    # Reload scheduled jobs from DB on startup
    with app.app_context():
        db.create_all()
        
        # Initialize token usage if not exists
        for platform in ['instagram', 'linkedin']:
            if not TokenUsage.query.filter_by(platform=platform).first():
                usage = TokenUsage(platform=platform, total_limit=200, used_today=0)
                db.session.add(usage)
        db.session.commit()
        
        # Load pending posts after tables are created
        try:
            pending = ScheduledPost.query.filter_by(status='scheduled').all()
            for p in pending:
                if p.scheduled_time > datetime.utcnow():
                    scheduler.add_job(execute_post, 'date', run_date=p.scheduled_time, args=[p.id], id=f'post_{p.id}', replace_existing=True)
                else:
                    # Missed schedule, mark failed
                    p.status = 'missed'
            db.session.commit()
        except Exception as e:
            print(f"Error loading scheduled posts: {e}")

    from .routes import main_bp
    from .auth import auth_bp
    from .collab_routes import collab_bp
    from .admin_routes import admin_bp
    from .training_routes import training_bp
    from .settings_routes import settings_bp
    from .webhook_routes import webhook_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(collab_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(webhook_bp)

    # Expose helper to schedule new job
    @app.before_request
    def ensure_upload_folder():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.schedule_post_job = lambda post_id, run_date: scheduler.add_job(execute_post, 'date', run_date=run_date, args=[post_id], id=f'post_{post_id}', replace_existing=True)

    return app
