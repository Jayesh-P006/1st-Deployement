"""
Instagram Webhook Handler for DM Automation
Handles incoming webhook events from Instagram for direct messages
"""
from flask import current_app, request
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
import threading

API_BASE = 'https://graph.facebook.com/v19.0'

def verify_webhook_signature(payload, signature):
    """
    Verify that the webhook request came from Instagram/Facebook
    
    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
    
    Returns:
        bool: True if signature is valid
    """
    app_secret = current_app.config.get('INSTAGRAM_APP_SECRET')
    if not app_secret:
        # If no app secret configured, skip verification (dev mode)
        current_app.logger.warning('INSTAGRAM_APP_SECRET not configured - skipping signature verification')
        return True
    
    if not signature:
        return False
    
    try:
        # Signature format: sha256=<signature>
        method, signature_hash = signature.split('=')
        
        # Calculate expected signature
        expected_signature = hmac.new(
            app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature_hash, expected_signature)
    except Exception as e:
        current_app.logger.error(f'Signature verification error: {e}')
        return False

def handle_webhook_verification(verify_token, challenge):
    """
    Handle webhook verification request from Instagram
    
    Args:
        verify_token: Token sent by Instagram
        challenge: Challenge string to echo back
    
    Returns:
        str: Challenge string if verification succeeds, None otherwise
    """
    expected_token = current_app.config.get('WEBHOOK_VERIFY_TOKEN')
    
    if verify_token == expected_token:
        current_app.logger.info('Webhook verification successful')
        return challenge
    else:
        current_app.logger.warning(f'Webhook verification failed. Expected: {expected_token}, Got: {verify_token}')
        return None


def _normalize_message_id(message_id, sender_id=None, timestamp=None, max_length=100):
    """Ensure instagram_message_id fits DB column (String(100))."""
    mid = str(message_id or '').strip()
    if not mid:
        mid = f"mid-{sender_id or 'unknown'}-{timestamp or int(time.time())}"
    
    # If too long, hash it to preserve uniqueness
    if len(mid) > max_length:
        # Use last 16 chars of the hash to preserve uniqueness
        import hashlib
        hash_suffix = hashlib.md5(mid.encode()).hexdigest()[:16]
        # Keep beginning + hash to stay under limit
        prefix_len = max_length - 17  # -1 for dash separator
        mid = mid[:prefix_len] + '-' + hash_suffix
    
    return mid

def send_instagram_message(recipient_id, message_text):
    """
    Send a message to Instagram user via Instagram Graph API
    
    Args:
        recipient_id: Instagram PSID (Page-Scoped ID)
        message_text: Message content to send
    
    Returns:
        dict: {'success': bool, 'message_id': str, 'error': str}
    """
    token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
    business_id = current_app.config.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if not token or not business_id:
        return {
            'success': False,
            'message_id': None,
            'error': 'Instagram credentials not configured'
        }
    
    # Use the business account id for the messages endpoint; "me" fails for IG DMs.
    endpoint = f"{API_BASE}/{business_id}/messages"
    
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text},
        'access_token': token
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'message_id': data.get('message_id'),
                'error': None
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('error', {}).get('message', response.text)
            error_code = error_data.get('error', {}).get('code')
            
            # Special handling for permission error
            if error_code == 3 or 'does not have the capability' in error_msg:
                error_msg = (
                    'Instagram messaging permission not granted. '
                    'Your app needs "instagram_manage_messages" permission from Meta. '
                    'Submit your app for review at: https://developers.facebook.com/apps/'
                )
            
            current_app.logger.error(f'Instagram send failed: {error_msg}')
            return {
                'success': False,
                'message_id': None,
                'error': f'Instagram API error: {error_msg}'
            }
    except Exception as e:
        current_app.logger.error(f'Instagram send exception: {e}')
        return {
            'success': False,
            'message_id': None,
            'error': str(e)
        }

def get_instagram_username(instagram_user_id):
    """
    Fetch Instagram username from user ID
    
    Args:
        instagram_user_id: Instagram PSID
    
    Returns:
        str: Username or None
    """
    token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
    
    if not token:
        current_app.logger.warning('Cannot fetch username: INSTAGRAM_ACCESS_TOKEN not configured')
        return None
    
    try:
        endpoint = f"{API_BASE}/{instagram_user_id}"
        params = {
            'fields': 'name,username,profile_pic',
            'access_token': token
        }
        
        response = requests.get(endpoint, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            username = data.get('username') or data.get('name')
            if username:
                current_app.logger.info(f'Fetched username for {instagram_user_id}: {username}')
            return username
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('error', {}).get('message', response.text)
            current_app.logger.warning(f'Failed to fetch username for {instagram_user_id}: {error_msg}')
            return None
    except Exception as e:
        current_app.logger.error(f'Error fetching username for {instagram_user_id}: {e}')
        return None

def process_instagram_message(sender_id, message_id, message_text, timestamp):
    """
    Process incoming Instagram DM and generate auto-reply
    
    Args:
        sender_id: Instagram PSID of the sender
        message_id: Instagram message ID
        message_text: The message content
        timestamp: Message timestamp (milliseconds)
    
    Returns:
        dict: Processing result
    """
    from .. import db
    from ..models import DMConversation, DMMessage
    from ..ai.rag_chat import generate_dm_response
    
    current_app.logger.info(f'Processing message from {sender_id}: {message_text[:50]}...')
    
    try:
        # Find or create conversation
        conversation = DMConversation.query.filter_by(instagram_user_id=sender_id).first()
        
        if not conversation:
            # New conversation - get username
            username = get_instagram_username(sender_id)
            conversation = DMConversation(
                instagram_user_id=sender_id,
                instagram_username=username,
                platform='instagram',
                message_count=0,
                auto_reply_count=0
            )
            db.session.add(conversation)
            db.session.flush()  # Get ID
        
        # Normalize message id to fit DB constraint
        message_id = _normalize_message_id(message_id, sender_id=sender_id, timestamp=timestamp)

        # Skip duplicates if already stored
        if DMMessage.query.filter_by(instagram_message_id=message_id).first():
            current_app.logger.info(f"Skip duplicate message_id={message_id}")
            return {
                'success': True,
                'replied': False,
                'reason': 'duplicate_message',
            }

        # Save incoming message
        incoming_msg = DMMessage(
            conversation_id=conversation.id,
            instagram_message_id=message_id,
            sender_type='user',
            message_text=message_text,
            is_auto_reply=False
        )
        db.session.add(incoming_msg)
        
        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        conversation.message_count += 1
        # Increment unread count if column exists
        try:
            conversation.unread_count = (conversation.unread_count or 0) + 1
        except AttributeError:
            pass  # Column doesn't exist yet
        
        db.session.commit()
        
        # Check if we should auto-reply using ChatSettings
        from ..models import ChatSettings
        from ..ai.gemini_service import should_auto_reply
        
        should_reply, reason = should_auto_reply(message_text, conversation)
        if not should_reply:
            current_app.logger.info(f'Not replying: {reason}')
            return {
                'success': True,
                'replied': False,
                'reason': reason,
            }

        app_obj = current_app._get_current_object()
        conversation_id = conversation.id

        def _send_reply_async():
            from .. import db as _db
            from ..models import DMConversation as _DMConversation, DMMessage as _DMMessage

            with app_obj.app_context():
                try:
                    conv = _DMConversation.query.get(conversation_id)
                    if not conv:
                        app_obj.logger.warning('Async reply: conversation missing')
                        return

                    # Use new RAG system for response generation
                    try:
                        reply_text = generate_dm_response(
                            message=message_text,
                            conversation_id=str(sender_id)
                        )
                        app_obj.logger.info(f"RAG response generated: {reply_text[:50]}...")
                    except Exception as rag_error:
                        app_obj.logger.error(f"RAG generation error: {rag_error}")
                        # Fallback to simple greeting
                        from ..ai.gemini_service import generate_fallback_response
                        reply_text = generate_fallback_response()

                    send_result = send_instagram_message(sender_id, reply_text)

                    outgoing_msg = _DMMessage(
                        conversation_id=conv.id,
                        instagram_message_id=send_result.get('message_id'),
                        sender_type='bot',
                        message_text=reply_text,
                        is_auto_reply=True,
                        gemini_prompt_used=None,  # RAG system doesn't expose prompts
                        gemini_response_time=None,  # RAG handles timing internally
                        sent_successfully=send_result.get('success', False),
                        error_message=send_result.get('error'),
                    )
                    _db.session.add(outgoing_msg)

                    conv.message_count = (conv.message_count or 0) + 1
                    if send_result.get('success'):
                        conv.auto_reply_count = (conv.auto_reply_count or 0) + 1

                    _db.session.commit()
                except Exception as e:
                    app_obj.logger.error(f'Async auto-reply error: {e}')
                    try:
                        _db.session.rollback()
                    except Exception:
                        pass

        threading.Thread(target=_send_reply_async, daemon=True).start()

        return {
            'success': True,
            'replied': True,
            'reason': 'Queued auto-reply',
        }
    
    except Exception as e:
        current_app.logger.error(f'Error processing message: {e}')
        db.session.rollback()
        return {
            'success': False,
            'replied': False,
            'error': str(e)
        }

def handle_webhook_event(event_data):
    """
    Process webhook event from Instagram
    
    Args:
        event_data: Webhook payload from Instagram
    
    Returns:
        dict: Processing result
    """
    try:
        # Instagram webhook structure:
        # {
        #   "object": "instagram",
        #   "entry": [{
        #     "id": "<page-id>",
        #     "time": 123456789,
        #     "messaging": [{
        #       "sender": {"id": "<psid>"},
        #       "recipient": {"id": "<page-id>"},
        #       "timestamp": 123456789,
        #       "message": {
        #         "mid": "<message-id>",
        #         "text": "<message-text>"
        #       }
        #     }]
        #   }]
        # }
        
        # Meta can send Instagram messaging webhooks with object "instagram" or "page"
        # depending on how the subscription is configured.
        obj_type = event_data.get('object')
        if obj_type not in {'instagram', 'page'}:
            current_app.logger.info(f"Webhook object '{obj_type}' received; attempting to parse anyway")
        
        results = []
        current_app.logger.info(f"Webhook payload received: {json.dumps(event_data)[:2000]}")
        
        def _extract_text_events(entry_obj):
            """Return a list of normalized events: {sender_id, timestamp, message_id, message_text}."""
            extracted = []

            def _add(sender_id, message_text, timestamp=None, message_id=None, source=None):
                if not sender_id:
                    current_app.logger.info('Skip event: missing sender_id')
                    return
                if not message_text:
                    current_app.logger.info('Skip event: empty message_text')
                    return
                # Fallback message id to avoid None/dup issues
                mid = message_id or f"auto-{timestamp or datetime.utcnow().timestamp()}-{sender_id}"
                extracted.append({
                    'sender_id': sender_id,
                    'timestamp': timestamp,
                    'message_id': mid,
                    'message_text': message_text,
                    'source': source,
                })

            # 1) Standard: entry.messaging[]
            for ev in (entry_obj.get('messaging') or []) if isinstance(entry_obj.get('messaging'), list) else []:
                sender_id = (ev.get('sender') or {}).get('id')
                timestamp = ev.get('timestamp')
                message = ev.get('message')
                if isinstance(message, dict):
                    message_id = message.get('mid') or message.get('id')
                    message_text = message.get('text') or ''
                    _add(sender_id, message_text, timestamp=timestamp, message_id=message_id, source='entry.messaging')

            # 2) Alternate: entry.changes[].value.*
            for change in (entry_obj.get('changes') or []) if isinstance(entry_obj.get('changes'), list) else []:
                value = change.get('value') or {}

                # 2a) value.messaging[]
                if isinstance(value.get('messaging'), list):
                    for ev in value.get('messaging') or []:
                        sender_id = (ev.get('sender') or {}).get('id')
                        timestamp = ev.get('timestamp')
                        message = ev.get('message')
                        if isinstance(message, dict):
                            message_id = message.get('mid') or message.get('id')
                            message_text = message.get('text') or ''
                            _add(sender_id, message_text, timestamp=timestamp, message_id=message_id, source='changes.messaging')

                # 2b) Some integrations deliver a single message-like object in value
                # Try common fields: value.from.id + value.message/text
                sender_id = None
                from_obj = value.get('from')
                if isinstance(from_obj, dict):
                    sender_id = from_obj.get('id')
                message_text = value.get('message') or value.get('text')
                if sender_id and isinstance(message_text, str) and message_text.strip():
                    _add(sender_id, message_text.strip(), timestamp=value.get('timestamp') or value.get('time'), message_id=value.get('id'), source='changes.value')

            return extracted

        for entry in event_data.get('entry', []) or []:
            extracted = _extract_text_events(entry)
            current_app.logger.info(f"Extracted {len(extracted)} text events from entry")
            for ev in extracted:
                try:
                    result = process_instagram_message(
                        ev['sender_id'],
                        ev.get('message_id'),
                        ev.get('message_text') or '',
                        ev.get('timestamp'),
                    )
                    results.append(result)
                except Exception as e:
                    current_app.logger.error(f"Error processing extracted event from {ev.get('source')}: {e}")
            
            # NEW: Handle comment events for automation
            changes = entry.get('changes', [])
            for change in changes:
                field = change.get('field')
                value = change.get('value', {})
                
                # Instagram comment webhook
                if field == 'comments':
                    try:
                        from ..automation_handlers import handle_comment_event
                        
                        comment_data = {
                            'id': value.get('id'),
                            'text': value.get('text', ''),
                            'from': value.get('from', {})
                        }
                        
                        # Get post data
                        media_id = value.get('media', {}).get('id') if isinstance(value.get('media'), dict) else value.get('media')
                        post_data = {
                            'id': media_id,
                            'caption': '',  # Could fetch this from API if needed
                            'permalink': ''
                        }
                        
                        # Process comment automation
                        automation_result = handle_comment_event(comment_data, post_data)
                        current_app.logger.info(f'Comment automation processed: {automation_result}')
                        
                        results.append({
                            'type': 'comment',
                            'comment_id': comment_data['id'],
                            'automation': automation_result
                        })
                    except Exception as comment_err:
                        current_app.logger.error(f'Comment automation error: {comment_err}')
                        results.append({
                            'type': 'comment',
                            'status': 'error',
                            'error': str(comment_err)
                        })

        if not results:
            current_app.logger.info('No processable messaging events found in webhook payload')
        
        return {
            'success': True,
            'processed': len(results),
            'results': results
        }
    
    except Exception as e:
        current_app.logger.error(f'Webhook event processing error: {e}')
        return {
            'success': False,
            'error': str(e)
        }
