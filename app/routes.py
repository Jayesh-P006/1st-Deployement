from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from datetime import datetime, timedelta, timezone
import os
from . import db
from .models import ScheduledPost, TokenUsage
from .auth import login_required

def convert_local_to_utc(local_dt, tz_name='Asia/Kolkata'):
    """Convert local datetime to UTC.
    
    For IST (Asia/Kolkata): UTC+5:30
    """
    # Define timezone offsets
    tz_offsets = {
        'Asia/Kolkata': timedelta(hours=5, minutes=30),  # IST
        'America/New_York': timedelta(hours=-5),  # EST
        'America/Los_Angeles': timedelta(hours=-8),  # PST
        'Europe/London': timedelta(hours=0),  # GMT
        'UTC': timedelta(hours=0),
    }
    
    offset = tz_offsets.get(tz_name, timedelta(hours=5, minutes=30))  # Default IST
    
    # If datetime is naive (no timezone), assume it's in local timezone
    if local_dt.tzinfo is None:
        # Subtract offset to get UTC
        utc_dt = local_dt - offset
        return utc_dt
    return local_dt

def convert_utc_to_local(utc_dt, tz_name='Asia/Kolkata'):
    """Convert UTC datetime to local time."""
    tz_offsets = {
        'Asia/Kolkata': timedelta(hours=5, minutes=30),
        'America/New_York': timedelta(hours=-5),
        'America/Los_Angeles': timedelta(hours=-8),
        'Europe/London': timedelta(hours=0),
        'UTC': timedelta(hours=0),
    }
    
    offset = tz_offsets.get(tz_name, timedelta(hours=5, minutes=30))
    return utc_dt + offset

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    posts = ScheduledPost.query.order_by(ScheduledPost.created_at.desc()).all()
    
    # Calculate stats
    total_posts = len(posts)
    posted = len([p for p in posts if p.status == 'posted'])
    scheduled = len([p for p in posts if p.status == 'scheduled'])
    failed = len([p for p in posts if p.status == 'failed'])
    success_rate = round((posted / total_posts * 100) if total_posts > 0 else 0, 1)
    
    # Token usage
    insta_usage = TokenUsage.query.filter_by(platform='instagram').first()
    linkedin_usage = TokenUsage.query.filter_by(platform='linkedin').first()
    
    return render_template('index.html', 
                         posts=posts, 
                         total_posts=total_posts,
                         posted=posted,
                         scheduled=scheduled,
                         failed=failed,
                         success_rate=success_rate,
                         insta_usage=insta_usage,
                         linkedin_usage=linkedin_usage)

@main_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        platform = request.form.get('platform')
        content = request.form.get('content', '').strip()
        scheduled_time_str = request.form.get('scheduled_time')
        image = request.files.get('image')

        if not platform or platform not in ['instagram', 'linkedin']:
            flash('Select a valid platform.', 'error')
            return redirect(url_for('main.new_post'))
        if not content:
            flash('Content is required.', 'error')
            return redirect(url_for('main.new_post'))
        if not scheduled_time_str:
            flash('Scheduled time is required.', 'error')
            return redirect(url_for('main.new_post'))

        try:
            # Parse local time from form and convert to UTC for storage
            local_time = datetime.fromisoformat(scheduled_time_str)
            tz_name = current_app.config.get('APP_TIMEZONE', 'Asia/Kolkata')
            scheduled_time = convert_local_to_utc(local_time, tz_name)
        except ValueError:
            flash('Invalid datetime format. Use YYYY-MM-DDTHH:MM.', 'error')
            return redirect(url_for('main.new_post'))

        image_paths = []
        images = request.files.getlist('image')
        if images:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            for img in images:
                if img and img.filename:
                    filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + img.filename.replace(' ', '_')
                    full_path = os.path.join(upload_folder, filename)
                    img.save(full_path)
                    image_paths.append(full_path)
        
        import json
        image_path_json = json.dumps(image_paths) if image_paths else None
        post = ScheduledPost(platform=platform, content=content, image_path=image_path_json, scheduled_time=scheduled_time)
        db.session.add(post)
        db.session.commit()

        # Schedule job
        current_app.schedule_post_job(post.id, post.scheduled_time)
        flash('Post scheduled successfully!', 'success')
        return redirect(url_for('main.index'))

    # Get token usage for display
    insta_usage = TokenUsage.query.filter_by(platform='instagram').first()
    linkedin_usage = TokenUsage.query.filter_by(platform='linkedin').first()
    
    return render_template('new_post.html', insta_usage=insta_usage, linkedin_usage=linkedin_usage)

@main_bp.route('/preview/<int:post_id>')
def preview_post(post_id):
    post = ScheduledPost.query.get_or_404(post_id)
    return render_template('preview.html', post=post)

@main_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = ScheduledPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        platform = request.form.get('platform')
        content = request.form.get('content', '').strip()
        scheduled_time_str = request.form.get('scheduled_time')
        image = request.files.get('image')

        if not platform or platform not in ['instagram', 'linkedin']:
            flash('Select a valid platform.', 'error')
            return redirect(url_for('main.edit_post', post_id=post_id))
        if not content:
            flash('Content is required.', 'error')
            return redirect(url_for('main.edit_post', post_id=post_id))
        if not scheduled_time_str:
            flash('Scheduled time is required.', 'error')
            return redirect(url_for('main.edit_post', post_id=post_id))

        try:
            # Parse local time from form and convert to UTC for storage
            local_time = datetime.fromisoformat(scheduled_time_str)
            tz_name = current_app.config.get('APP_TIMEZONE', 'Asia/Kolkata')
            scheduled_time = convert_local_to_utc(local_time, tz_name)
        except ValueError:
            flash('Invalid datetime format. Use YYYY-MM-DDTHH:MM.', 'error')
            return redirect(url_for('main.edit_post', post_id=post_id))

        # Update post fields
        post.platform = platform
        post.content = content
        post.scheduled_time = scheduled_time
        
        # Handle new image uploads
        images = request.files.getlist('image')
        if images and any(img.filename for img in images):
            import json
            image_paths = []
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            for img in images:
                if img and img.filename:
                    filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + img.filename.replace(' ', '_')
                    full_path = os.path.join(upload_folder, filename)
                    img.save(full_path)
                    image_paths.append(full_path)
            if image_paths:
                post.image_path = json.dumps(image_paths)

        db.session.commit()

        # Reschedule job
        try:
            from . import scheduler
            scheduler.remove_job(f'post_{post_id}')
        except:
            pass
        current_app.schedule_post_job(post.id, post.scheduled_time)
        
        flash('Post updated successfully!', 'success')
        return redirect(url_for('main.index'))

    # Get token usage for display
    insta_usage = TokenUsage.query.filter_by(platform='instagram').first()
    linkedin_usage = TokenUsage.query.filter_by(platform='linkedin').first()
    
    # Convert stored UTC time to local time for the edit form
    tz_name = current_app.config.get('APP_TIMEZONE', 'Asia/Kolkata')
    local_scheduled_time = convert_utc_to_local(post.scheduled_time, tz_name)
    
    return render_template('edit_post.html', post=post, insta_usage=insta_usage, linkedin_usage=linkedin_usage, local_scheduled_time=local_scheduled_time)

@main_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = ScheduledPost.query.get_or_404(post_id)
    
    # Remove scheduled job if exists
    try:
        from . import scheduler
        scheduler.remove_job(f'post_{post_id}')
    except:
        pass
    
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully.', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/api/token-status')
@login_required
def token_status():
    insta = TokenUsage.query.filter_by(platform='instagram').first()
    linkedin = TokenUsage.query.filter_by(platform='linkedin').first()
    return jsonify({
        'instagram': {
            'used': insta.used_today if insta else 0,
            'total': insta.total_limit if insta else 200,
            'remaining': insta.remaining() if insta else 200
        },
        'linkedin': {
            'used': linkedin.used_today if linkedin else 0,
            'total': linkedin.total_limit if linkedin else 200,
            'remaining': linkedin.remaining() if linkedin else 200
        }
    })

@main_bp.route('/api/account-status')
def account_status():
    """Get connection status for Instagram and LinkedIn accounts"""
    from .social.instagram import check_instagram_account_status
    from .social.linkedin import check_linkedin_account_status
    from flask import current_app
    from .models import DMConversation, DMMessage
    
    instagram_status = check_instagram_account_status()
    linkedin_status = check_linkedin_account_status()

    # Webhook status (lightweight heuristics)
    # - configured: required secrets/tokens exist
    # - linked_previously: we have ever stored a DM message/conversation (means webhook payloads reached us)
    webhook_configured = bool(
        current_app.config.get('WEBHOOK_VERIFY_TOKEN')
        and current_app.config.get('INSTAGRAM_APP_SECRET')
    )

    webhook_linked_previously = None
    webhook_last_event_at = None
    try:
        # Prefer last message timestamp if present
        last_msg = DMMessage.query.order_by(DMMessage.created_at.desc()).first()
        if last_msg:
            webhook_linked_previously = True
            webhook_last_event_at = last_msg.created_at.isoformat() if last_msg.created_at else None
        else:
            # Fall back to conversation existence
            webhook_linked_previously = DMConversation.query.count() > 0
    except Exception:
        # DB may be unavailable/misconfigured; return unknown rather than failing the endpoint
        webhook_linked_previously = None
        webhook_last_event_at = None

    if isinstance(instagram_status, dict):
        instagram_status['webhook_configured'] = webhook_configured
        instagram_status['webhook_linked_previously'] = webhook_linked_previously
        instagram_status['webhook_last_event_at'] = webhook_last_event_at
    
    return jsonify({
        'instagram': instagram_status,
        'linkedin': linkedin_status
    })

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

