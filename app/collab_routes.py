from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session
from datetime import datetime
from pytz import timezone as tz
import os
import json
from . import db
from .models import PostDraft, User, Comment, Activity, ScheduledPost, TokenUsage
from .auth import login_required, role_required, get_current_user
from .ai.vision_service import analyze_image_for_caption, analyze_multiple_images
from .utils import download_image_to_uploads

collab_bp = Blueprint('collab', __name__, url_prefix='/collab')

@collab_bp.route('/drafts')
@login_required
def drafts():
    current_user = get_current_user()
    
    # With new position-based system, show all drafts to all active users for collaboration
    # Lead and Co-Lead can see and manage everything
    # Members can see all drafts to work on content, media, and PR tasks
    # Exclude scheduled and published posts - they should only appear in "Scheduled" section
    if current_user.position in ['Lead', 'Co-Lead'] or current_user.role == 'admin':
        # Leaders and admins see all drafts (except scheduled/published)
        drafts = PostDraft.query.filter(
            PostDraft.workflow_status.in_(['draft', 'review', 'approved'])
        ).order_by(PostDraft.created_at.desc()).all()
    else:
        # Members see all drafts (for collaborative workflow, except scheduled/published)
        # They can work on content, media, and PR sponsorship
        drafts = PostDraft.query.filter(
            PostDraft.workflow_status.in_(['draft', 'review', 'approved'])
        ).order_by(PostDraft.created_at.desc()).all()
    
    return render_template('collab/drafts.html', 
                         drafts=drafts,
                         current_user=current_user)

@collab_bp.route('/draft/new', methods=['GET', 'POST'])
@login_required
def new_draft():
    current_user = get_current_user()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        platform = request.form.get('platform', '')
        theme = request.form.get('theme', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title or not platform:
            flash('Title and platform are required.', 'error')
            return redirect(url_for('collab.new_draft'))
        
        draft = PostDraft(
            title=title,
            platform=platform,
            theme=theme if theme else None,
            description=description if description else None,
            created_by_id=current_user.id
        )
        db.session.add(draft)
        db.session.flush()
        
        # Log activity
        activity = Activity(
            draft_id=draft.id,
            user_id=current_user.id,
            action='created_draft',
            description=f'Created draft: {title}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Draft created successfully! Teams can now start working on it.', 'success')
        return redirect(url_for('collab.edit_draft', draft_id=draft.id))
    
    return render_template('collab/new_draft.html',
                         current_user=current_user)

@collab_bp.route('/draft/<int:draft_id>', methods=['GET', 'POST'])
@login_required
def edit_draft(draft_id):
    current_user = get_current_user()
    draft = PostDraft.query.get_or_404(draft_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Content update (Creative team)
        if action == 'update_content' and current_user.can_edit_content():
            content = request.form.get('content', '').strip()
            if content:
                draft.content = content
                if draft.content_status == 'pending':
                    draft.content_status = 'completed'
                    draft.content_completed_at = datetime.utcnow()
                
                activity = Activity(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    action='updated_content',
                    description='Updated post content'
                )
                db.session.add(activity)
                flash('Content updated successfully!', 'success')
        
        # Media update (Production team)
        elif action == 'update_media' and current_user.can_edit_media():
            images = request.files.getlist('image')
            image_url = request.form.get('image_url', '').strip()

            new_paths = []
            if images and any(img.filename for img in images):
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                for img in images:
                    if img and img.filename:
                        filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + img.filename.replace(' ', '_')
                        full_path = os.path.join(upload_folder, filename)
                        img.save(full_path)
                        new_paths.append(full_path)

            # Optional: add image from URL
            if image_url:
                upload_folder = current_app.config['UPLOAD_FOLDER']
                saved = download_image_to_uploads(image_url, upload_folder)
                if saved:
                    new_paths.append(saved)

            if new_paths:
                # Merge with existing images if present
                existing = []
                if draft.image_path:
                    try:
                        existing = json.loads(draft.image_path) if draft.image_path.startswith('[') else [draft.image_path]
                    except Exception:
                        existing = []
                all_paths = existing + new_paths
                draft.image_path = json.dumps(all_paths)
                if draft.media_status == 'pending':
                    draft.media_status = 'completed'
                    draft.media_completed_at = datetime.utcnow()

                activity = Activity(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    action='uploaded_media',
                    description=f'Uploaded {len(new_paths)} image(s)'
                )
                db.session.add(activity)
                flash('Media added successfully!', 'success')
        
        # Tags update (PR & Sponsorship team)
        elif action == 'update_tags' and current_user.can_edit_tags():
            tags = request.form.get('collaboration_tags', '').strip()
            if tags:
                # Convert comma-separated to JSON array
                tags_list = [t.strip() for t in tags.split(',') if t.strip()]
                draft.collaboration_tags = json.dumps(tags_list)
                if draft.tags_status == 'pending':
                    draft.tags_status = 'completed'
                    draft.tags_completed_at = datetime.utcnow()
                
                activity = Activity(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    action='updated_tags',
                    description='Updated collaboration tags'
                )
                db.session.add(activity)
                flash('Collaboration tags updated successfully!', 'success')
        
        # Submit for review
        elif action == 'submit_review':
            if draft.is_ready_for_review():
                if not draft.scheduled_time:
                    flash('Please set a scheduled time before submitting for review.', 'error')
                    return redirect(url_for('collab.edit_draft', draft_id=draft_id))
                    
                draft.workflow_status = 'review'
                activity = Activity(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    action='submitted_review',
                    description='Submitted draft for review'
                )
                db.session.add(activity)
                flash('Draft submitted for review!', 'success')
            else:
                flash('Content and media must be completed before submitting for review.', 'error')
        
        # Set scheduled time
        elif action == 'set_schedule_time':
            scheduled_time_str = request.form.get('scheduled_time')
            if scheduled_time_str:
                try:
                    # Parse the datetime from user input (naive datetime)
                    naive_dt = datetime.fromisoformat(scheduled_time_str)
                    
                    # Get the app timezone
                    app_tz_name = current_app.config.get('APP_TIMEZONE', 'Asia/Kolkata')
                    app_tz = tz(app_tz_name)
                    
                    # Localize the naive datetime to app timezone
                    localized_dt = app_tz.localize(naive_dt)
                    
                    # Convert to UTC for storage in database
                    utc_dt = localized_dt.astimezone(tz('UTC'))
                    
                    # Store as naive UTC (remove tzinfo to match existing pattern)
                    draft.scheduled_time = utc_dt.replace(tzinfo=None)
                    
                    activity = Activity(
                        draft_id=draft.id,
                        user_id=current_user.id,
                        action='set_schedule_time',
                        description=f'Set scheduled time to {naive_dt.strftime("%Y-%m-%d %H:%M")} {app_tz_name}'
                    )
                    db.session.add(activity)
                    flash(f'Scheduled time set for {naive_dt.strftime("%Y-%m-%d %H:%M")} {app_tz_name}', 'success')
                except ValueError as e:
                    flash(f'Invalid datetime format: {str(e)}', 'error')
            else:
                flash('Scheduled time is required.', 'error')
        
        # Approve draft
        elif action == 'approve' and current_user.can_approve():
            if not draft.scheduled_time:
                flash('Cannot approve: scheduled time is not set.', 'error')
                return redirect(url_for('collab.edit_draft', draft_id=draft_id))
            
            # Create scheduled post immediately
            post = ScheduledPost(
                platform=draft.platform,
                content=draft.content,
                image_path=draft.image_path,
                collaboration_tags=draft.collaboration_tags,
                scheduled_time=draft.scheduled_time
            )
            db.session.add(post)
            db.session.flush()
            
            draft.scheduled_post_id = post.id
            draft.workflow_status = 'scheduled'
            draft.approved_by_id = current_user.id
            draft.approved_at = datetime.utcnow()
            draft.content_status = 'approved'
            draft.media_status = 'approved'
            draft.tags_status = 'approved'
            
            # Schedule job
            current_app.schedule_post_job(post.id, draft.scheduled_time)
            
            activity = Activity(
                draft_id=draft.id,
                user_id=current_user.id,
                action='approved_and_scheduled',
                description=f'Approved and scheduled for {draft.scheduled_time.strftime("%Y-%m-%d %H:%M")} UTC'
            )
            db.session.add(activity)
            flash('Draft approved and scheduled successfully!', 'success')
        
        # Request revision
        elif action == 'request_revision' and current_user.can_approve():
            revision_notes = request.form.get('revision_notes', '').strip()
            draft.workflow_status = 'draft'
            
            if revision_notes:
                comment = Comment(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    content=revision_notes,
                    comment_type='revision'
                )
                db.session.add(comment)
            
            activity = Activity(
                draft_id=draft.id,
                user_id=current_user.id,
                action='requested_revision',
                description='Requested revisions'
            )
            db.session.add(activity)
            flash('Revision requested. Draft sent back to teams.', 'success')
        
        # Add comment
        elif action == 'add_comment':
            comment_content = request.form.get('comment', '').strip()
            if comment_content:
                comment = Comment(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    content=comment_content,
                    comment_type='general'
                )
                db.session.add(comment)
                flash('Comment added successfully!', 'success')
        
        draft.updated_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('collab.edit_draft', draft_id=draft_id))
    
    # GET request - display draft
    comments = Comment.query.filter_by(draft_id=draft_id).order_by(Comment.created_at.desc()).all()
    activities = Activity.query.filter_by(draft_id=draft_id).order_by(Activity.created_at.desc()).limit(20).all()
    
    return render_template('collab/edit_draft.html',
                         draft=draft,
                         current_user=current_user,
                         comments=comments,
                         activities=activities)

@collab_bp.route('/draft/<int:draft_id>/schedule', methods=['POST'])
@login_required
@role_required('admin', 'approver')
def schedule_draft(draft_id):
    """Legacy endpoint - scheduling now happens automatically on approval"""
    current_user = get_current_user()
    draft = PostDraft.query.get_or_404(draft_id)
    
    # This endpoint is now mainly for re-scheduling if needed
    if draft.workflow_status not in ['approved', 'scheduled']:
        flash('Only approved drafts can be scheduled.', 'error')
        return redirect(url_for('collab.edit_draft', draft_id=draft_id))
    
    scheduled_time_str = request.form.get('scheduled_time')
    if not scheduled_time_str:
        flash('Scheduled time is required.', 'error')
        return redirect(url_for('collab.edit_draft', draft_id=draft_id))
    
    try:
        scheduled_time = datetime.fromisoformat(scheduled_time_str)
    except ValueError:
        flash('Invalid datetime format.', 'error')
        return redirect(url_for('collab.edit_draft', draft_id=draft_id))
    
    # Update existing scheduled post or create new one
    if draft.scheduled_post_id:
        post = ScheduledPost.query.get(draft.scheduled_post_id)
        post.scheduled_time = scheduled_time
    else:
        post = ScheduledPost(
            platform=draft.platform,
            content=draft.content,
            image_path=draft.image_path,
            collaboration_tags=draft.collaboration_tags,
            scheduled_time=scheduled_time
        )
        db.session.add(post)
        db.session.flush()
        draft.scheduled_post_id = post.id
    
    draft.scheduled_time = scheduled_time
    draft.workflow_status = 'scheduled'
    
    # Schedule job
    current_app.schedule_post_job(post.id, scheduled_time)
    
    activity = Activity(
        draft_id=draft.id,
        user_id=current_user.id,
        action='rescheduled_post',
        description=f'Re-scheduled post for {scheduled_time.strftime("%Y-%m-%d %H:%M")} UTC'
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('Post re-scheduled successfully!', 'success')
    return redirect(url_for('main.index'))

@collab_bp.route('/draft/<int:draft_id>/delete', methods=['POST'])
@login_required
def delete_draft(draft_id):
    current_user = get_current_user()
    draft = PostDraft.query.get_or_404(draft_id)
    
    # Only creator, admin, or approver can delete
    if draft.created_by_id != current_user.id and not current_user.can_approve():
        flash('You do not have permission to delete this draft.', 'error')
        return redirect(url_for('collab.drafts'))
    
    db.session.delete(draft)
    db.session.commit()
    
    flash('Draft deleted successfully.', 'success')
    return redirect(url_for('collab.drafts'))

@collab_bp.route('/api/draft/<int:draft_id>/generate-caption', methods=['POST'])
@login_required
def generate_caption_from_images(draft_id):
    """API endpoint to generate caption from uploaded images using Gemini Vision"""
    draft = PostDraft.query.get_or_404(draft_id)
    
    try:
        # Check if Gemini API is configured
        if not current_app.config.get('GEMINI_API_KEY'):
            return jsonify({
                'success': False,
                'error': 'Gemini API not configured. Please add GEMINI_API_KEY to environment variables.'
            }), 503
        
        if not draft.image_path:
            return jsonify({
                'success': False,
                'error': 'No images uploaded yet'
            }), 400
        
        image_paths = json.loads(draft.image_path)
        
        # Add rate limiting check - max 5 caption generations per minute
        from datetime import timedelta
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_activities = Activity.query.filter(
            Activity.action == 'generated_caption',
            Activity.created_at >= one_minute_ago
        ).count()
        
        if recent_activities >= 5:
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Please wait a minute before generating more captions.'
            }), 429
        
        if len(image_paths) == 1:
            result = analyze_image_for_caption(
                image_paths[0],
                platform=draft.platform,
                draft_title=draft.title
            )
        else:
            result = analyze_multiple_images(
                image_paths,
                platform=draft.platform,
                draft_title=draft.title
            )
        
        if result['success']:
            # Log the caption generation
            activity = Activity(
                draft_id=draft.id,
                user_id=get_current_user().id,
                action='generated_caption',
                description='Generated caption using Gemini Vision' if not result.get('is_fallback') else 'Used fallback caption template'
            )
            db.session.add(activity)
            db.session.commit()
            
            response_data = {
                'success': True,
                'caption': result['caption']
            }
            
            # Add warning if it's a fallback caption
            if result.get('is_fallback'):
                response_data['warning'] = result.get('warning', 'Using template caption. Please customize.')
                response_data['is_fallback'] = True
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Caption generation error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@collab_bp.route('/api/draft/<int:draft_id>/comments', methods=['GET'])
@login_required
def get_comments(draft_id):
    """API endpoint to fetch latest comments for real-time updates"""
    draft = PostDraft.query.get_or_404(draft_id)
    comments = Comment.query.filter_by(draft_id=draft_id).order_by(Comment.created_at.desc()).all()
    
    comments_data = [{
        'id': c.id,
        'author': c.author.full_name if c.author else 'Unknown',
        'content': c.content,
        'comment_type': c.comment_type,
        'created_at': c.created_at.strftime('%b %d, %H:%M'),
        'timestamp': c.created_at.isoformat()
    } for c in comments]
    
    return jsonify({
        'success': True,
        'comments': comments_data,
        'count': len(comments_data)
    })
@collab_bp.route('/api/draft/<int:draft_id>/auto-save', methods=['POST'])
@login_required
def auto_save_draft(draft_id):
    """API endpoint for auto-saving draft content, media, or tags"""
    current_user = get_current_user()
    draft = PostDraft.query.get_or_404(draft_id)
    
    try:
        data = request.get_json()
        section = data.get('section')  # 'content', 'media', 'tags'
        
        if section == 'content' and current_user.can_edit_content():
            content = data.get('content', '').strip()
            if content:
                draft.content = content
                if draft.content_status == 'pending':
                    draft.content_status = 'completed'
                    draft.content_completed_at = datetime.utcnow()
                
                activity = Activity(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    action='auto_saved_content',
                    description='Auto-saved content'
                )
                db.session.add(activity)
        
        elif section == 'tags' and current_user.can_edit_tags():
            tags = data.get('tags', [])
            if tags:
                draft.collaboration_tags = json.dumps(tags)
                if draft.tags_status == 'pending':
                    draft.tags_status = 'completed'
                    draft.tags_completed_at = datetime.utcnow()
                
                activity = Activity(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    action='auto_saved_tags',
                    description='Auto-saved tags'
                )
                db.session.add(activity)
        
        draft.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{section.capitalize()} auto-saved',
            'completion': draft.get_completion_percentage()
        })
    
    except Exception as e:
        current_app.logger.error(f'Auto-save error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@collab_bp.route('/api/draft/<int:draft_id>/remove-media', methods=['POST'])
@login_required
def remove_media(draft_id):
    """API endpoint to remove a specific media file"""
    current_user = get_current_user()
    draft = PostDraft.query.get_or_404(draft_id)
    
    if not current_user.can_edit_media():
        return jsonify({
            'success': False,
            'error': 'Permission denied'
        }), 403
    
    try:
        data = request.get_json()
        media_index = data.get('index')
        
        if draft.image_path:
            images = json.loads(draft.image_path)
            if 0 <= media_index < len(images):
                removed_image = images.pop(media_index)
                
                # Try to delete the file from disk
                try:
                    if os.path.exists(removed_image):
                        os.remove(removed_image)
                except Exception as file_err:
                    current_app.logger.warning(f'Could not delete file: {file_err}')
                
                # Update draft
                if images:
                    draft.image_path = json.dumps(images)
                else:
                    draft.image_path = None
                    draft.media_status = 'pending'
                
                activity = Activity(
                    draft_id=draft.id,
                    user_id=current_user.id,
                    action='removed_media',
                    description=f'Removed media file'
                )
                db.session.add(activity)
                draft.updated_at = datetime.utcnow()
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Media removed',
                    'remaining_count': len(images)
                })
        
        return jsonify({
            'success': False,
            'error': 'Invalid media index'
        }), 400
    
    except Exception as e:
        current_app.logger.error(f'Remove media error: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500