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
    if len(mid) > max_length:
        mid = mid[:max_length]
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
    
    endpoint = f"{API_BASE}/me/messages"
    
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
            return {
                'success': False,
                'message_id': None,
                'error': f'Instagram API error: {error_msg}'
            }
    except Exception as e:
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
        return None
    
    try:
        endpoint = f"{API_BASE}/{instagram_user_id}"
        params = {
            'fields': 'name,username',
            'access_token': token
        }
        
        response = requests.get(endpoint, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('username') or data.get('name')
        else:
            return None
    except:
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
    from ..ai.gemini_service import generate_reply, should_auto_reply, generate_fallback_response
    
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
        
        db.session.commit()
        
        # Check if we should auto-reply.
        # IMPORTANT: Reply generation/sending can be slow; we do it asynchronously so webhook responses stay fast.
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

                    reply_result = generate_reply(conv, message_text)
                    if not reply_result.get('success'):
                        app_obj.logger.error(f"Gemini error: {reply_result.get('error')}")
                        reply_text = generate_fallback_response()
                    else:
                        reply_text = reply_result.get('reply')

                    send_result = send_instagram_message(sender_id, reply_text)

                    outgoing_msg = _DMMessage(
                        conversation_id=conv.id,
                        instagram_message_id=send_result.get('message_id'),
                        sender_type='bot',
                        message_text=reply_text,
                        is_auto_reply=True,
                        gemini_prompt_used=reply_result.get('prompt'),
                        gemini_response_time=reply_result.get('response_time'),
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
