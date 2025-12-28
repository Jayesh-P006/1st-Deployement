"""
Example Integration: Automated DM Response System
==================================================

This file demonstrates how to integrate the RAG chat system into your
Instagram DM webhook handlers. Copy relevant sections to your actual
dm_routes.py or instagram_dm_sync.py file.

"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from config import Config
from app.models import db, DMConversation, DMMessage
from app.ai.rag_chat import generate_dm_response

logger = logging.getLogger(__name__)

# Create blueprint
dm_blueprint = Blueprint('dm', __name__)


@dm_blueprint.route('/webhook/instagram/dm', methods=['POST'])
def instagram_dm_webhook():
    """
    Handle Instagram DM webhook events with automated RAG responses.
    
    TOKEN OPTIMIZATION: The RAG system automatically:
    1. Filters greetings (0 tokens)
    2. Uses k=1 retrieval (minimal context)
    3. Rate limits to 30 req/min
    """
    try:
        data = request.json
        logger.info(f"Received DM webhook: {data}")
        
        # Verify webhook signature (IMPORTANT for security)
        # signature = request.headers.get('X-Hub-Signature-256')
        # if not verify_webhook_signature(request.data, signature):
        #     return jsonify({'error': 'Invalid signature'}), 403
        
        # Process each entry
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                
                # Handle incoming message
                if 'message' in messaging_event:
                    handle_incoming_message(messaging_event)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def handle_incoming_message(messaging_event: dict):
    """
    Process an incoming DM and generate automated response.
    
    This function:
    1. Extracts message details
    2. Saves to database (optional)
    3. Generates RAG response
    4. Sends reply via Instagram API
    
    Args:
        messaging_event: Instagram messaging event data
    """
    try:
        # Extract message details
        sender_id = messaging_event['sender']['id']
        recipient_id = messaging_event['recipient']['id']
        message_data = messaging_event['message']
        
        message_id = message_data.get('mid')
        message_text = message_data.get('text', '')
        timestamp = messaging_event.get('timestamp')
        
        # Skip if no text (e.g., image/sticker only)
        if not message_text:
            logger.info(f"Skipping non-text message from {sender_id}")
            return
        
        logger.info(f"Processing DM from {sender_id}: {message_text}")
        
        # Optional: Save to database
        save_incoming_message(
            sender_id=sender_id,
            message_id=message_id,
            message_text=message_text,
            timestamp=timestamp
        )
        
        # Generate response using RAG system
        # CRITICAL: This is where the magic happens!
        response_text = generate_dm_response(
            message=message_text,
            conversation_id=sender_id  # Use sender_id to track conversation
        )
        
        logger.info(f"Generated response: {response_text}")
        
        # Send response via Instagram API
        send_instagram_message(
            recipient_id=sender_id,
            message_text=response_text
        )
        
        # Optional: Save outgoing message to database
        save_outgoing_message(
            recipient_id=sender_id,
            message_text=response_text
        )
        
        logger.info(f"Successfully replied to {sender_id}")
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")


def send_instagram_message(recipient_id: str, message_text: str) -> dict:
    """
    Send a message to a user via Instagram Direct Message API.
    
    Args:
        recipient_id: Instagram user ID (sender's ID from webhook)
        message_text: Message content to send
        
    Returns:
        API response dict
    """
    import requests
    
    url = "https://graph.facebook.com/v18.0/me/messages"
    
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text},
        'messaging_type': 'RESPONSE',  # Responding to user message
        'access_token': Config.INSTAGRAM_ACCESS_TOKEN
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Message sent successfully: {result}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Instagram message: {str(e)}")
        raise


def save_incoming_message(
    sender_id: str,
    message_id: str,
    message_text: str,
    timestamp: int
):
    """
    Save incoming message to database (optional).
    
    This helps track conversation history and analytics.
    """
    try:
        # Get or create conversation
        conversation = DMConversation.query.filter_by(
            instagram_user_id=sender_id
        ).first()
        
        if not conversation:
            conversation = DMConversation(
                instagram_user_id=sender_id,
                platform='instagram',
                last_message_at=datetime.fromtimestamp(timestamp / 1000)
            )
            db.session.add(conversation)
            db.session.flush()
        
        # Save message
        message = DMMessage(
            conversation_id=conversation.id,
            instagram_message_id=message_id,
            sender_id=sender_id,
            message_text=message_text,
            direction='incoming',
            created_at=datetime.fromtimestamp(timestamp / 1000)
        )
        db.session.add(message)
        
        # Update conversation
        conversation.last_message_at = message.created_at
        conversation.last_message_text = message_text[:200]
        
        db.session.commit()
        logger.info(f"Saved incoming message to database: {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to save message to database: {str(e)}")
        db.session.rollback()


def save_outgoing_message(recipient_id: str, message_text: str):
    """
    Save outgoing (bot) message to database (optional).
    """
    try:
        conversation = DMConversation.query.filter_by(
            instagram_user_id=recipient_id
        ).first()
        
        if conversation:
            message = DMMessage(
                conversation_id=conversation.id,
                sender_id='bot',  # Bot identifier
                message_text=message_text,
                direction='outgoing',
                created_at=datetime.utcnow()
            )
            db.session.add(message)
            
            conversation.last_message_at = message.created_at
            conversation.last_message_text = message_text[:200]
            
            db.session.commit()
            logger.info(f"Saved outgoing message to database")
    
    except Exception as e:
        logger.error(f"Failed to save outgoing message: {str(e)}")
        db.session.rollback()


# ============================================================
# OPTIONAL: Manual Response Override
# ============================================================

@dm_blueprint.route('/api/dm/manual-reply', methods=['POST'])
def manual_reply():
    """
    Allow manual override of auto-replies.
    
    Useful for admin intervention or testing.
    """
    data = request.json
    
    recipient_id = data.get('recipient_id')
    message_text = data.get('message')
    
    if not recipient_id or not message_text:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        send_instagram_message(recipient_id, message_text)
        save_outgoing_message(recipient_id, message_text)
        
        return jsonify({
            'success': True,
            'message': 'Manual reply sent successfully'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# ============================================================
# OPTIONAL: Disable Auto-Reply for Specific Users
# ============================================================

# Add this to your database models (app/models.py):
# class DMConversation(db.Model):
#     ...
#     auto_reply_enabled = db.Column(db.Boolean, default=True)

def should_auto_reply(sender_id: str) -> bool:
    """
    Check if auto-reply is enabled for this conversation.
    
    Returns:
        True if auto-reply should be sent, False otherwise
    """
    conversation = DMConversation.query.filter_by(
        instagram_user_id=sender_id
    ).first()
    
    if conversation:
        return conversation.auto_reply_enabled
    
    return True  # Default: enabled for new conversations


@dm_blueprint.route('/api/dm/toggle-auto-reply', methods=['POST'])
def toggle_auto_reply():
    """
    Enable/disable auto-reply for a specific conversation.
    
    Useful for VIP users or when human intervention is needed.
    """
    data = request.json
    user_id = data.get('user_id')
    enabled = data.get('enabled', True)
    
    conversation = DMConversation.query.filter_by(
        instagram_user_id=user_id
    ).first()
    
    if conversation:
        conversation.auto_reply_enabled = enabled
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Auto-reply {'enabled' if enabled else 'disabled'}"
        })
    
    return jsonify({'error': 'Conversation not found'}), 404


# ============================================================
# TESTING ENDPOINT
# ============================================================

@dm_blueprint.route('/api/test-dm-response', methods=['POST'])
def test_dm_response():
    """
    Test the RAG response system without sending actual DMs.
    
    Useful for debugging and tuning responses.
    """
    data = request.json
    test_message = data.get('message', 'Hi there!')
    
    try:
        response = generate_dm_response(
            message=test_message,
            conversation_id='test_conversation'
        )
        
        return jsonify({
            'query': test_message,
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# ============================================================
# WEBHOOK VERIFICATION (Required by Instagram)
# ============================================================

@dm_blueprint.route('/webhook/instagram/dm', methods=['GET'])
def verify_webhook():
    """
    Verify webhook with Instagram.
    
    Instagram will call this endpoint to verify your webhook URL.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == Config.WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed")
        return 'Forbidden', 403
