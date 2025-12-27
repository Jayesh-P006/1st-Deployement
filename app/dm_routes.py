"""
Direct Message Routes - Dedicated DM Management
Separated from settings for better organization
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import json
from datetime import datetime, timedelta
from . import db
from .models import DMConversation, DMMessage
from .auth import login_required
from .social.instagram_webhooks import send_instagram_message, _normalize_message_id
from .social.instagram_dm_sync import sync_previous_instagram_dms, InstagramGraphPermissionError

dm_bp = Blueprint('dm', __name__, url_prefix='/dm')


@dm_bp.route('/')
@login_required
def conversations():
    """View DM conversations in inbox-style layout"""
    status_filter = request.args.get('status', 'all')
    selected_conversation_id = request.args.get('conversation_id', type=int)

    query = DMConversation.query
    
    if status_filter != 'all':
        query = query.filter_by(conversation_status=status_filter)
    
    conversations_list = query.order_by(DMConversation.last_message_at.desc()).all()

    selected_conversation = None
    messages = []

    if conversations_list:
        if selected_conversation_id:
            selected_conversation = next((c for c in conversations_list if c.id == selected_conversation_id), None)
        if not selected_conversation:
            selected_conversation = conversations_list[0]

        messages = selected_conversation.messages.order_by(DMMessage.created_at.asc()).all()
    
    # Get status counts
    status_counts = {
        'all': DMConversation.query.count(),
        'active': DMConversation.query.filter_by(conversation_status='active').count(),
        'resolved': DMConversation.query.filter_by(conversation_status='resolved').count(),
        'archived': DMConversation.query.filter_by(conversation_status='archived').count(),
    }
    
    return render_template(
        'dm/conversations.html',
        conversations=conversations_list,
        selected_conversation=selected_conversation,
        messages=messages,
        status_filter=status_filter,
        status_counts=status_counts,
        DMMessage=DMMessage,
    )


@dm_bp.route('/api/messages/<int:conversation_id>')
@login_required
def api_get_messages(conversation_id):
    """API endpoint to fetch messages for a conversation (for AJAX polling)"""
    conversation = DMConversation.query.get_or_404(conversation_id)
    messages = conversation.messages.order_by(DMMessage.created_at.asc()).all()
    
    return jsonify({
        'success': True,
        'conversation_id': conversation.id,
        'message_count': len(messages),
        'messages': [{
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message_text': msg.message_text,
            'is_auto_reply': msg.is_auto_reply,
            'sent_successfully': msg.sent_successfully,
            'error_message': msg.error_message,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at_time': msg.created_at.strftime('%H:%M'),
        } for msg in messages]
    })


@dm_bp.route('/api/conversations')
@login_required
def api_get_conversations():
    """API endpoint to fetch conversation list with latest message (for AJAX polling)"""
    status_filter = request.args.get('status', 'all')
    
    query = DMConversation.query
    if status_filter != 'all':
        query = query.filter_by(conversation_status=status_filter)
    
    conversations = query.order_by(DMConversation.last_message_at.desc()).all()
    
    return jsonify({
        'success': True,
        'conversations': [{
            'id': conv.id,
            'instagram_username': conv.instagram_username,
            'instagram_user_id': conv.instagram_user_id,
            'conversation_status': conv.conversation_status,
            'message_count': conv.message_count,
            'auto_reply_count': conv.auto_reply_count,
            'last_message_at': conv.last_message_at.strftime('%Y-%m-%d %H:%M:%S') if conv.last_message_at else None,
            'last_message_preview': (conv.messages.order_by(DMMessage.created_at.desc()).first().message_text[:70] 
                                    if conv.messages.first() else ''),
        } for conv in conversations]
    })


@dm_bp.route('/sync', methods=['POST'])
@login_required
def sync_conversations():
    """Sync previous Instagram DMs via Graph API"""
    try:
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

    return redirect(url_for('dm.conversations'))


@dm_bp.route('/<int:conversation_id>/reply', methods=['POST'])
@login_required
def reply_conversation(conversation_id):
    """Send a manual reply to an Instagram DM thread"""
    conversation = DMConversation.query.get_or_404(conversation_id)
    message_text = (request.form.get('message_text') or '').strip()

    if not message_text:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('dm.conversations', conversation_id=conversation_id))

    # Send via Instagram Graph
    send_result = send_instagram_message(conversation.instagram_user_id, message_text)

    # Record the outgoing message regardless of success so history is visible
    message_id = _normalize_message_id(
        send_result.get('message_id') or f"manual-{conversation_id}-{int(datetime.utcnow().timestamp())}",
        sender_id=conversation.instagram_user_id,
    )

    outgoing = DMMessage(
        conversation_id=conversation.id,
        instagram_message_id=message_id,
        sender_type='bot',
        message_text=message_text,
        is_auto_reply=False,
        sent_successfully=send_result.get('success', False),
        error_message=send_result.get('error'),
    )
    db.session.add(outgoing)

    conversation.message_count = (conversation.message_count or 0) + 1
    conversation.last_message_at = datetime.utcnow()

    try:
        db.session.commit()
        if send_result.get('success'):
            flash('Reply sent.', 'success')
        else:
            flash(f"Reply saved but send failed: {send_result.get('error')}", 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Could not save reply: {e}', 'error')

    return redirect(url_for('dm.conversations', conversation_id=conversation_id))


@dm_bp.route('/<int:conversation_id>/status', methods=['POST'])
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
    
    return redirect(url_for('dm.conversations', conversation_id=conversation_id))
