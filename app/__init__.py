from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import os
import atexit

from config import Config

db = SQLAlchemy()
scheduler = None  # Will be initialized once

def get_scheduler():
    """Get or create the scheduler singleton."""
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler(daemon=True)
    return scheduler

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

    # Add filter to convert UTC to local timezone for display
    from datetime import timedelta
    @app.template_filter('to_local')
    def to_local_filter(utc_dt):
        """Convert UTC datetime to local timezone for display."""
        if utc_dt is None:
            return ''
        tz_name = app.config.get('APP_TIMEZONE', 'Asia/Kolkata')
        tz_offsets = {
            'Asia/Kolkata': timedelta(hours=5, minutes=30),
            'America/New_York': timedelta(hours=-5),
            'America/Los_Angeles': timedelta(hours=-8),
            'Europe/London': timedelta(hours=0),
            'UTC': timedelta(hours=0),
        }
        offset = tz_offsets.get(tz_name, timedelta(hours=5, minutes=30))
        local_dt = utc_dt + offset
        return local_dt.strftime('%b %d, %Y %H:%M')

    # Initialize scheduler only once
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        # Ensure scheduler shuts down when app exits
        atexit.register(lambda: sched.shutdown(wait=False))

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

    def check_and_execute_pending_posts():
        """Periodic job to check for posts that should be executed."""
        with app.app_context():
            now = datetime.utcnow()
            pending = ScheduledPost.query.filter(
                ScheduledPost.status == 'scheduled',
                ScheduledPost.scheduled_time <= now
            ).all()
            
            for post in pending:
                try:
                    token_used = 0
                    if post.platform == 'instagram':
                        token_used = post_to_instagram(post)
                    elif post.platform == 'linkedin':
                        token_used = post_to_linkedin(post)
                    post.status = 'posted'
                    post.token_used = token_used
                    
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
        
        # Add a periodic job that checks every minute for pending posts
        # This is more reliable than scheduling individual jobs that can be lost
        if not sched.get_job('check_pending_posts'):
            sched.add_job(
                check_and_execute_pending_posts,
                'interval',
                minutes=1,
                id='check_pending_posts',
                replace_existing=True
            )
        
        # Also schedule individual jobs for immediate precision
        try:
            pending = ScheduledPost.query.filter_by(status='scheduled').all()
            now = datetime.utcnow()
            for p in pending:
                if p.scheduled_time > now:
                    sched.add_job(execute_post, 'date', run_date=p.scheduled_time, args=[p.id], id=f'post_{p.id}', replace_existing=True)
        except Exception as e:
            print(f"Error loading scheduled posts: {e}")

    from .routes import main_bp
    from .auth import auth_bp
    from .collab_routes import collab_bp
    from .admin_routes import admin_bp
    from .rag_routes import rag_bp
    from .settings_routes import settings_bp
    from .webhook_routes import webhook_bp
    from .dm_routes import dm_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(collab_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(rag_bp)  # RAG system status pages
    app.register_blueprint(settings_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(dm_bp)

    # Expose helper to schedule new job
    @app.before_request
    def ensure_upload_folder():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.schedule_post_job = lambda post_id, run_date: sched.add_job(execute_post, 'date', run_date=run_date, args=[post_id], id=f'post_{post_id}', replace_existing=True)

    return app
