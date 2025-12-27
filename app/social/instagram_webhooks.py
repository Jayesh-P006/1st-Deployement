"""
Instagram Webhook Handler for DM Automation
Handles incoming webhook events from Instagram for direct messages
"""
from flask import current_app, request
import requests
import json
import hmac
import hashlib
from datetime import datetime

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
    from ..models import DMConversation, DMMessage, ChatSettings
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
        
        # Check if we should auto-reply
        should_reply, reason = should_auto_reply(message_text, conversation)
        
        if not should_reply:
            current_app.logger.info(f'Not replying: {reason}')
            return {
                'success': True,
                'replied': False,
                'reason': reason
            }
        
        # Generate reply using Gemini
        reply_result = generate_reply(conversation, message_text)
        
        if not reply_result['success']:
            current_app.logger.error(f"Gemini error: {reply_result['error']}")
            # Use fallback message
            reply_text = generate_fallback_response()
        else:
            reply_text = reply_result['reply']
        
        # Send reply via Instagram API
        send_result = send_instagram_message(sender_id, reply_text)
        
        # Save outgoing message
        outgoing_msg = DMMessage(
            conversation_id=conversation.id,
            instagram_message_id=send_result.get('message_id'),
            sender_type='bot',
            message_text=reply_text,
            is_auto_reply=True,
            gemini_prompt_used=reply_result.get('prompt'),
            gemini_response_time=reply_result.get('response_time'),
            sent_successfully=send_result['success'],
            error_message=send_result.get('error')
        )
        db.session.add(outgoing_msg)
        
        # Update conversation
        conversation.message_count += 1
        if send_result['success']:
            conversation.auto_reply_count += 1
        
        db.session.commit()
        
        return {
            'success': True,
            'replied': send_result['success'],
            'reply_text': reply_text,
            'error': send_result.get('error')
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
        
        for entry in event_data.get('entry', []):
            # Common format: entry.messaging = [{ sender, recipient, timestamp, message: { mid, text } }]
            messaging_events = entry.get('messaging')

            # Alternate format: entry.changes[].value.messaging = [...]
            if not messaging_events:
                messaging_events = []
                for change in entry.get('changes', []) or []:
                    value = change.get('value') or {}
                    if isinstance(value.get('messaging'), list):
                        messaging_events.extend(value.get('messaging'))

            for event in messaging_events or []:
                sender_id = (event.get('sender') or {}).get('id')
                timestamp = event.get('timestamp')

                message = event.get('message')
                if not isinstance(message, dict):
                    continue

                # Mid can be present as 'mid' (common) or sometimes as 'id'
                message_id = message.get('mid') or message.get('id')
                message_text = message.get('text') or ''

                # Ignore non-text messages for now (attachments, reactions, etc.)
                if not (message_text and sender_id):
                    continue

                result = process_instagram_message(
                    sender_id,
                    message_id,
                    message_text,
                    timestamp
                )
                results.append(result)

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
