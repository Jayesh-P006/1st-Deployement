"""
Chat Control Settings Routes
Manage auto-reply settings, rate limits, and automation controls
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import json
from datetime import datetime, timedelta
from . import db
from .models import ChatSettings, DMConversation, DMMessage
from .auth import login_required, role_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

def get_or_create_settings():
    """Get existing settings or create default"""
    settings = ChatSettings.query.first()
    if not settings:
        settings = ChatSettings(
            auto_reply_enabled=False,
            auto_comment_enabled=False,
            reply_rate_limit=10,
            comment_rate_limit=20,
            business_hours_only=False,
            business_hours_start="09:00",
            business_hours_end="18:00"
        )
        db.session.add(settings)
        db.session.commit()
    return settings

@settings_bp.route('/')
@login_required
def index():
    """View chat control settings"""
    settings = get_or_create_settings()
    
    # Parse JSON fields
    blacklist = []
    whitelist = []
    
    if settings.blacklist_keywords:
        try:
            blacklist = json.loads(settings.blacklist_keywords)
        except:
            pass
    
    if settings.whitelist_users:
        try:
            whitelist = json.loads(settings.whitelist_users)
        except:
            pass
    
    # Get statistics
    total_conversations = DMConversation.query.count()
    active_conversations = DMConversation.query.filter_by(conversation_status='active').count()
    
    # Auto-replies in last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(hours=24)
    auto_replies_24h = DMMessage.query.filter(
        DMMessage.is_auto_reply == True,
        DMMessage.created_at >= one_day_ago
    ).count()
    
    # Auto-replies in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    auto_replies_1h = DMMessage.query.filter(
        DMMessage.is_auto_reply == True,
        DMMessage.created_at >= one_hour_ago
    ).count()
    
    stats = {
        'total_conversations': total_conversations,
        'active_conversations': active_conversations,
        'auto_replies_24h': auto_replies_24h,
        'auto_replies_1h': auto_replies_1h,
        'rate_limit_1h': settings.reply_rate_limit,
        'remaining_1h': max(0, settings.reply_rate_limit - auto_replies_1h)
    }
    
    return render_template('settings/chat_controls.html', 
                         settings=settings, 
                         blacklist=blacklist,
                         whitelist=whitelist,
                         stats=stats)

@settings_bp.route('/update', methods=['POST'])
@login_required
@role_required('admin', 'approver')
def update_settings():
    """Update chat control settings"""
    settings = get_or_create_settings()
    
    # Toggle switches
    settings.auto_reply_enabled = request.form.get('auto_reply_enabled') == 'on'
    settings.auto_comment_enabled = request.form.get('auto_comment_enabled') == 'on'
    settings.business_hours_only = request.form.get('business_hours_only') == 'on'
    
    # Rate limits
    try:
        settings.reply_rate_limit = int(request.form.get('reply_rate_limit', 10))
        settings.comment_rate_limit = int(request.form.get('comment_rate_limit', 20))
    except ValueError:
        flash('Invalid rate limit values.', 'error')
        return redirect(url_for('settings.index'))
    
    # Business hours
    settings.business_hours_start = request.form.get('business_hours_start', '09:00')
    settings.business_hours_end = request.form.get('business_hours_end', '18:00')
    
    # Messages
    default_greeting = request.form.get('default_greeting', '').strip()
    fallback_message = request.form.get('fallback_message', '').strip()
    
    if default_greeting:
        settings.default_greeting = default_greeting
    if fallback_message:
        settings.fallback_message = fallback_message
    
    # Blacklist keywords
    blacklist_str = request.form.get('blacklist_keywords', '').strip()
    if blacklist_str:
        blacklist = [kw.strip() for kw in blacklist_str.split(',') if kw.strip()]
        settings.blacklist_keywords = json.dumps(blacklist)
    else:
        settings.blacklist_keywords = None
    
    # Whitelist users
    whitelist_str = request.form.get('whitelist_users', '').strip()
    if whitelist_str:
        whitelist = [user.strip() for user in whitelist_str.split(',') if user.strip()]
        settings.whitelist_users = json.dumps(whitelist)
    else:
        settings.whitelist_users = None
    
    db.session.commit()
    
    flash('Chat control settings updated successfully!', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/toggle/<setting_name>', methods=['POST'])
@login_required
@role_required('admin', 'approver')
def toggle_setting(setting_name):
    """Quick toggle for boolean settings"""
    settings = get_or_create_settings()
    
    if setting_name == 'auto_reply':
        settings.auto_reply_enabled = not settings.auto_reply_enabled
        status = 'enabled' if settings.auto_reply_enabled else 'disabled'
        flash(f'Auto-reply {status}.', 'success')
    elif setting_name == 'auto_comment':
        settings.auto_comment_enabled = not settings.auto_comment_enabled
        status = 'enabled' if settings.auto_comment_enabled else 'disabled'
        flash(f'Auto-comment {status}.', 'success')
    elif setting_name == 'business_hours':
        settings.business_hours_only = not settings.business_hours_only
        status = 'enabled' if settings.business_hours_only else 'disabled'
        flash(f'Business hours restriction {status}.', 'success')
    else:
        flash('Invalid setting name.', 'error')
    
    db.session.commit()
    
    return redirect(url_for('settings.index'))

@settings_bp.route('/api/status')
@login_required
def api_status():
    """API endpoint for real-time status"""
    settings = get_or_create_settings()
    
    # Get current usage
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    auto_replies_1h = DMMessage.query.filter(
        DMMessage.is_auto_reply == True,
        DMMessage.created_at >= one_hour_ago
    ).count()
    
    return jsonify({
        'auto_reply_enabled': settings.auto_reply_enabled,
        'auto_comment_enabled': settings.auto_comment_enabled,
        'business_hours_only': settings.business_hours_only,
        'reply_rate_limit': settings.reply_rate_limit,
        'auto_replies_1h': auto_replies_1h,
        'remaining_1h': max(0, settings.reply_rate_limit - auto_replies_1h),
        'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
    })

@settings_bp.route('/conversations')
@login_required
def conversations():
    """View DM conversations and history"""
    status_filter = request.args.get('status', 'all')
    
    query = DMConversation.query
    
    if status_filter != 'all':
        query = query.filter_by(conversation_status=status_filter)
    
    conversations_list = query.order_by(DMConversation.last_message_at.desc()).all()
    
    # Get status counts
    status_counts = {
        'all': DMConversation.query.count(),
        'active': DMConversation.query.filter_by(conversation_status='active').count(),
        'resolved': DMConversation.query.filter_by(conversation_status='resolved').count(),
        'archived': DMConversation.query.filter_by(conversation_status='archived').count(),
    }
    
    return render_template('dm/conversations.html', 
                         conversations=conversations_list,
                         status_filter=status_filter,
                         status_counts=status_counts)


@settings_bp.route('/conversations/sync', methods=['POST'])
@login_required
def sync_conversations():
    """Sync previous Instagram DMs via Graph API (best-effort)."""
    try:
        from .social.instagram_dm_sync import sync_previous_instagram_dms, InstagramGraphPermissionError

        max_conversations = int(request.form.get('max_conversations', 50))
        max_messages = int(request.form.get('max_messages', 50))

        summary = sync_previous_instagram_dms(
            max_conversations=max_conversations,
            max_messages_per_conversation=max_messages,
        )
        flash(
            f"Sync complete: {summary['messages_created']} messages added (skipped {summary['messages_skipped_existing']} existing).",
            'success'
        )
    except InstagramGraphPermissionError as e:
        if getattr(e, 'required_permission', None) == 'read_mailbox':
            flash(
                "Sync failed: Meta blocked access to inbox history. Your token/app needs the extended permission 'read_mailbox' (requires Meta App Review) to read previous conversations. "
                "Until that permission is granted, we can only rely on webhooks for new messages.",
                'error'
            )
        else:
            flash(f"Sync failed: {e}", 'error')
    except Exception as e:
        flash(f"Sync failed: {e}", 'error')

    return redirect(url_for('settings.conversations'))

@settings_bp.route('/conversations/<int:conversation_id>')
@login_required
def view_conversation(conversation_id):
    """View detailed conversation history"""
    conversation = DMConversation.query.get_or_404(conversation_id)
    messages = conversation.messages.order_by(DMMessage.created_at.asc()).all()
    
    return render_template('dm/conversation_detail.html', 
                         conversation=conversation,
                         messages=messages)

@settings_bp.route('/conversations/<int:conversation_id>/status', methods=['POST'])
@login_required
def update_conversation_status(conversation_id):
    """Update conversation status"""
    conversation = DMConversation.query.get_or_404(conversation_id)
    new_status = request.form.get('status', 'active')
    
    if new_status in ['active', 'resolved', 'archived']:
        conversation.conversation_status = new_status
        db.session.commit()
        flash(f'Conversation status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'error')
    
    return redirect(url_for('settings.view_conversation', conversation_id=conversation_id))
