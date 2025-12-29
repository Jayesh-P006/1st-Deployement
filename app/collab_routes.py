from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session
from datetime import datetime
import os
import json
from . import db
from .models import PostDraft, User, Comment, Activity, ScheduledPost, TokenUsage
from .auth import login_required, role_required, get_current_user
from .ai.vision_service import analyze_image_for_caption, analyze_multiple_images

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
            if images and any(img.filename for img in images):
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
                    draft.image_path = json.dumps(image_paths)
                    if draft.media_status == 'pending':
                        draft.media_status = 'completed'
                        draft.media_completed_at = datetime.utcnow()
                    
                    activity = Activity(
                        draft_id=draft.id,
                        user_id=current_user.id,
                        action='uploaded_media',
                        description=f'Uploaded {len(image_paths)} image(s)'
                    )
                    db.session.add(activity)
                    flash('Media uploaded successfully!', 'success')
        
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
                flash('All sections must be completed before submitting for review.', 'error')
        
        # Approve draft
        elif action == 'approve' and current_user.can_approve():
            draft.workflow_status = 'approved'
            draft.approved_by_id = current_user.id
            draft.approved_at = datetime.utcnow()
            draft.content_status = 'approved'
            draft.media_status = 'approved'
            draft.tags_status = 'approved'
            
            activity = Activity(
                draft_id=draft.id,
                user_id=current_user.id,
                action='approved_draft',
                description='Approved draft for scheduling'
            )
            db.session.add(activity)
            flash('Draft approved! Ready to schedule.', 'success')
        
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
    current_user = get_current_user()
    draft = PostDraft.query.get_or_404(draft_id)
    
    if draft.workflow_status != 'approved':
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
    
    # Create scheduled post
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
        action='scheduled_post',
        description=f'Scheduled post for {scheduled_time.strftime("%Y-%m-%d %H:%M")} UTC'
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('Post scheduled successfully!', 'success')
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
        if not draft.image_path:
            return jsonify({
                'success': False,
                'error': 'No images uploaded yet'
            }), 400
        
        image_paths = json.loads(draft.image_path)
        
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
            return jsonify({
                'success': True,
                'caption': result['caption']
            })
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
