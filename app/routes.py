from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from datetime import datetime
import os
from . import db
from .models import ScheduledPost, TokenUsage
from .auth import login_required

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
            # Assume input is local time; convert to UTC by treating as naive and subtracting offset if needed.
            # Simplified: treat input as UTC directly for now.
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
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
            scheduled_time = datetime.fromisoformat(scheduled_time_str)
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
    
    return render_template('edit_post.html', post=post, insta_usage=insta_usage, linkedin_usage=linkedin_usage)

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
    
    instagram_status = check_instagram_account_status()
    linkedin_status = check_linkedin_account_status()
    
    return jsonify({
        'instagram': instagram_status,
        'linkedin': linkedin_status
    })

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

