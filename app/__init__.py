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
    
    # Ensure uploads folder exists and is properly configured
    import os
    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
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

    def execute_post(post_id):
        with app.app_context():
            post = ScheduledPost.query.get(post_id)
            if not post or post.status != 'scheduled':
                return
            try:
                token_used = 0
                if post.platform == 'instagram':
                    token_used = post_to_instagram(post)
                else:
                    raise ValueError(f'Unsupported platform: {post.platform}')
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
                    else:
                        raise ValueError(f'Unsupported platform: {post.platform}')
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
        if not TokenUsage.query.filter_by(platform='instagram').first():
            usage = TokenUsage(platform='instagram', total_limit=200, used_today=0)
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
    from .status_api import status_bp
    from .automation_routes import automation_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(collab_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(rag_bp)  # RAG system status pages
    app.register_blueprint(settings_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(dm_bp)
    app.register_blueprint(status_bp)  # System status API
    app.register_blueprint(automation_bp)  # Automation Suite
    def ensure_upload_folder():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.schedule_post_job = lambda post_id, run_date: sched.add_job(execute_post, 'date', run_date=run_date, args=[post_id], id=f'post_{post_id}', replace_existing=True)

    # Startup validation and helpful warnings
    try:
        public_url = app.config.get('PUBLIC_URL', '')
        if public_url:
            is_https = public_url.lower().startswith('https://')
            is_local = ('127.0.0.1' in public_url) or ('localhost' in public_url)
            if not is_https:
                print("[WARN] PUBLIC_URL is not HTTPS. Instagram requires HTTPS for image_url.")
            if is_local:
                print("[WARN] PUBLIC_URL points to localhost. Instagram cannot fetch local URLs. Set PUBLIC_URL or RAILWAY_PUBLIC_DOMAIN to your deployed domain.")
        else:
            print("[WARN] PUBLIC_URL is empty. Set PUBLIC_URL or RAILWAY_PUBLIC_DOMAIN in environment.")

        # Ensure uploads folder exists
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        except Exception as e:
            print(f"[WARN] Could not create uploads folder: {e}")

        # Check Instagram credentials presence
        if not app.config.get('INSTAGRAM_ACCESS_TOKEN') or not app.config.get('INSTAGRAM_BUSINESS_ACCOUNT_ID'):
            print("[WARN] Instagram credentials missing. Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID.")
    except Exception as _:
        pass

    return app
