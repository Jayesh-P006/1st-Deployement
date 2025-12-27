"""
Webhook Routes for Instagram DM Integration
Handles webhook verification and incoming webhook events
"""
from flask import Blueprint, request, jsonify, current_app
from .social.instagram_webhooks import handle_webhook_verification, handle_webhook_event, verify_webhook_signature

webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

@webhook_bp.route('/instagram', methods=['GET', 'POST'])
def instagram_webhook():
    """
    Instagram webhook endpoint
    GET: Webhook verification
    POST: Webhook events
    """
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token:
            result = handle_webhook_verification(token, challenge)
            if result:
                current_app.logger.info('Instagram webhook verified successfully')
                return result, 200
            else:
                current_app.logger.warning('Instagram webhook verification failed')
                return 'Verification failed', 403
        
        return 'Invalid request', 400
    
    elif request.method == 'POST':
        # Webhook event
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        # Verify signature
        if not verify_webhook_signature(request.get_data(), signature):
            current_app.logger.warning('Invalid webhook signature')
            return 'Invalid signature', 403
        
        # Process event
        try:
            event_data = request.get_json()
            current_app.logger.info(f'Received webhook event: {event_data}')

            # Process immediately so incoming DMs are stored right away.
            # Any slow work (AI reply / outgoing message) is handled asynchronously inside the handler.
            result = handle_webhook_event(event_data)
            current_app.logger.info(f'Webhook processed: {result}')
            return jsonify({'status': 'received', 'processed': result.get('processed', 0)}), 200
        
        except Exception as e:
            current_app.logger.error(f'Webhook processing error: {e}')
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    return 'Method not allowed', 405

@webhook_bp.route('/test', methods=['POST'])
def test_webhook():
    """Test webhook processing with sample data"""
    if not current_app.debug:
        return 'Test endpoint only available in debug mode', 403
    
    sample_event = {
        "object": "instagram",
        "entry": [{
            "id": "test-page-id",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "test-user-123"},
                "recipient": {"id": "test-page-id"},
                "timestamp": 1234567890,
                "message": {
                    "mid": "test-message-id",
                    "text": "This is a test message"
                }
            }]
        }]
    }
    
    result = handle_webhook_event(sample_event)
    return jsonify(result), 200
