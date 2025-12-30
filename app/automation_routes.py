"""
Automation Routes - Centralized hub for all automation features
Handles Auto-Comment Reply, Comment-to-DM triggers, and DM automation
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
import json
from datetime import datetime, timedelta
from . import db
from .models import AutoReplySettings, CommentTrigger, AutomationLog, CommentDMTracker, ChatSettings
from .auth import login_required, role_required

automation_bp = Blueprint('automation', __name__, url_prefix='/automations')


@automation_bp.route('/')
@login_required
def dashboard():
    """Main automation dashboard with 3 feature cards"""
    # Get settings summary for dashboard
    auto_reply_settings = AutoReplySettings.query.filter_by(platform='instagram').first()
    active_triggers = CommentTrigger.query.filter_by(is_active=True).count()
    dm_settings = ChatSettings.query.first()
    
    # Get recent activity stats
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_logs = AutomationLog.query.filter(AutomationLog.created_at >= last_24h).all()
    
    stats = {
        'auto_comment_active': auto_reply_settings.is_active if auto_reply_settings else False,
        'active_triggers': active_triggers,
        'dm_auto_reply_active': dm_settings.auto_reply_enabled if dm_settings else False,
        'comments_replied_24h': len([l for l in recent_logs if l.automation_type == 'auto_comment_reply']),
        'dms_sent_24h': len([l for l in recent_logs if l.automation_type == 'comment_to_dm']),
        'dm_replies_24h': len([l for l in recent_logs if l.automation_type == 'dm_auto_reply']),
    }
    
    return render_template('automation/dashboard.html', stats=stats)


# ============= AUTO-COMMENT REPLY FEATURE =============

@automation_bp.route('/auto-comment')
@login_required
def auto_comment_settings():
    """Configure auto-reply to comments"""
    settings = AutoReplySettings.query.filter_by(platform='instagram').first()
    
    if not settings:
        # Create default settings
        settings = AutoReplySettings(platform='instagram')
        db.session.add(settings)
        db.session.commit()
    
    # Get recent activity
    recent_logs = AutomationLog.query.filter_by(
        automation_type='auto_comment_reply'
    ).order_by(AutomationLog.created_at.desc()).limit(20).all()
    
    return render_template('automation/auto_comment.html', 
                         settings=settings,
                         recent_logs=recent_logs)


@automation_bp.route('/auto-comment/update', methods=['POST'])
@login_required
def update_auto_comment_settings():
    """Update auto-comment reply settings"""
    settings = AutoReplySettings.query.filter_by(platform='instagram').first()
    
    if not settings:
        settings = AutoReplySettings(platform='instagram')
        db.session.add(settings)
    
    # Update settings from form
    settings.is_active = request.form.get('is_active') == 'on'
    settings.tone = request.form.get('tone', 'friendly')
    settings.delay_seconds = int(request.form.get('delay_seconds', 30))
    settings.use_rag = request.form.get('use_rag') == 'on'
    settings.fallback_message = request.form.get('fallback_message', '').strip()
    settings.max_replies_per_hour = int(request.form.get('max_replies_per_hour', 20))
    
    # Handle ignore keywords (comma-separated)
    ignore_keywords_raw = request.form.get('ignore_keywords', '').strip()
    if ignore_keywords_raw:
        keywords = [k.strip() for k in ignore_keywords_raw.split(',') if k.strip()]
        settings.ignore_keywords = json.dumps(keywords)
    else:
        settings.ignore_keywords = None
    
    settings.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Auto-comment settings updated! Feature is now {"ACTIVE" if settings.is_active else "INACTIVE"}.', 
          'success' if settings.is_active else 'info')
    return redirect(url_for('automation.auto_comment_settings'))


# ============= COMMENT-TO-DM TRIGGER FEATURE =============

@automation_bp.route('/comment-to-dm')
@login_required
def comment_to_dm_triggers():
    """Manage keyword triggers for Comment-to-DM automation"""
    triggers = CommentTrigger.query.order_by(CommentTrigger.created_at.desc()).all()
    
    # Get recent activity
    recent_logs = AutomationLog.query.filter_by(
        automation_type='comment_to_dm'
    ).order_by(AutomationLog.created_at.desc()).limit(20).all()
    
    return render_template('automation/comment_to_dm.html', 
                         triggers=triggers,
                         recent_logs=recent_logs)


@automation_bp.route('/comment-to-dm/add', methods=['POST'])
@login_required
def add_comment_trigger():
    """Add new keyword trigger"""
    keyword = request.form.get('keyword', '').strip().upper()
    dm_response = request.form.get('dm_response', '').strip()
    use_rag = request.form.get('use_rag') == 'on'
    
    if not keyword:
        flash('Keyword is required!', 'error')
        return redirect(url_for('automation.comment_to_dm_triggers'))
    
    # Check if keyword already exists
    existing = CommentTrigger.query.filter_by(keyword=keyword).first()
    if existing:
        flash(f'Keyword "{keyword}" already exists!', 'error')
        return redirect(url_for('automation.comment_to_dm_triggers'))
    
    if not use_rag and not dm_response:
        flash('Either provide a DM response or enable RAG generation!', 'error')
        return redirect(url_for('automation.comment_to_dm_triggers'))
    
    # Create trigger
    trigger = CommentTrigger(
        keyword=keyword,
        dm_response=dm_response or 'Generated by AI',
        use_rag=use_rag,
        is_active=True,
        platform='instagram'
    )
    db.session.add(trigger)
    db.session.commit()
    
    flash(f'Trigger "{keyword}" created successfully! 🚀', 'success')
    return redirect(url_for('automation.comment_to_dm_triggers'))


@automation_bp.route('/comment-to-dm/toggle/<int:trigger_id>', methods=['POST'])
@login_required
def toggle_comment_trigger(trigger_id):
    """Toggle trigger active status"""
    trigger = CommentTrigger.query.get_or_404(trigger_id)
    trigger.is_active = not trigger.is_active
    trigger.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': trigger.is_active
    })


@automation_bp.route('/comment-to-dm/delete/<int:trigger_id>', methods=['POST'])
@login_required
def delete_comment_trigger(trigger_id):
    """Delete a trigger"""
    trigger = CommentTrigger.query.get_or_404(trigger_id)
    keyword = trigger.keyword
    db.session.delete(trigger)
    db.session.commit()
    
    flash(f'Trigger "{keyword}" deleted successfully.', 'success')
    return redirect(url_for('automation.comment_to_dm_triggers'))


@automation_bp.route('/comment-to-dm/edit/<int:trigger_id>', methods=['POST'])
@login_required
def edit_comment_trigger(trigger_id):
    """Update an existing trigger"""
    trigger = CommentTrigger.query.get_or_404(trigger_id)
    
    trigger.dm_response = request.form.get('dm_response', '').strip()
    trigger.use_rag = request.form.get('use_rag') == 'on'
    trigger.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Trigger "{trigger.keyword}" updated successfully!', 'success')
    return redirect(url_for('automation.comment_to_dm_triggers'))


# ============= ANALYTICS & LOGS =============

@automation_bp.route('/logs')
@login_required
def automation_logs():
    """View all automation activity logs"""
    automation_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    query = AutomationLog.query
    
    if automation_type != 'all':
        query = query.filter_by(automation_type=automation_type)
    
    logs = query.order_by(AutomationLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get stats
    total_logs = AutomationLog.query.count()
    success_rate = 0
    if total_logs > 0:
        successful = AutomationLog.query.filter_by(success=True).count()
        success_rate = round((successful / total_logs) * 100, 1)
    
    return render_template('automation/logs.html',
                         logs=logs,
                         automation_type=automation_type,
                         total_logs=total_logs,
                         success_rate=success_rate)


@automation_bp.route('/stats')
@login_required
def automation_stats():
    """Dashboard with automation analytics"""
    # Get time-based stats
    today = datetime.utcnow().date()
    last_7_days = datetime.utcnow() - timedelta(days=7)
    last_30_days = datetime.utcnow() - timedelta(days=30)
    
    stats = {
        'today': {
            'total': AutomationLog.query.filter(
                db.func.date(AutomationLog.created_at) == today
            ).count(),
            'auto_comment': AutomationLog.query.filter(
                db.func.date(AutomationLog.created_at) == today,
                AutomationLog.automation_type == 'auto_comment_reply'
            ).count(),
            'comment_to_dm': AutomationLog.query.filter(
                db.func.date(AutomationLog.created_at) == today,
                AutomationLog.automation_type == 'comment_to_dm'
            ).count(),
        },
        'week': {
            'total': AutomationLog.query.filter(
                AutomationLog.created_at >= last_7_days
            ).count(),
        },
        'month': {
            'total': AutomationLog.query.filter(
                AutomationLog.created_at >= last_30_days
            ).count(),
        },
        'triggers': {
            'total': CommentTrigger.query.count(),
            'active': CommentTrigger.query.filter_by(is_active=True).count(),
        }
    }
    
    # Get top triggers
    top_triggers = CommentTrigger.query.order_by(
        CommentTrigger.times_triggered.desc()
    ).limit(10).all()
    
    return render_template('automation/stats.html',
                         stats=stats,
                         top_triggers=top_triggers)
