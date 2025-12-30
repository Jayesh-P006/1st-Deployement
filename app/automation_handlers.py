"""
Automation Handlers - Core logic for processing automation events
Called by webhook receivers to handle auto-comment replies and comment-to-DM triggers
"""
from flask import current_app
import json
import time
import requests
from datetime import datetime
from .models import (
    AutoReplySettings, CommentTrigger, AutomationLog, 
    CommentDMTracker, db
)
from .ai.rag_chat import query_rag_system
from .social.instagram_webhooks import send_instagram_message
import threading


def handle_comment_event(comment_data, post_data):
    """
    Handle incoming comment webhook event
    Triggers both auto-comment reply and comment-to-DM automations
    
    Args:
        comment_data: {
            'id': str,
            'text': str,
            'from': {'id': str, 'username': str}
        }
        post_data: {
            'id': str,
            'caption': str,
            'permalink': str
        }
    
    Returns:
        dict: Processing results
    """
    start_time = time.time()
    results = {
        'auto_comment_processed': False,
        'comment_to_dm_processed': False,
        'errors': []
    }
    
    try:
        comment_id = comment_data.get('id')
        comment_text = comment_data.get('text', '').strip()
        user_data = comment_data.get('from', {})
        user_id = user_data.get('id')
        username = user_data.get('username', 'User')
        
        post_id = post_data.get('id')
        post_caption = post_data.get('caption', '')
        
        if not comment_text or not user_id:
            current_app.logger.warning('Invalid comment data')
            return results
        
        # Process in separate threads to not block webhook response
        # 1. Auto-Comment Reply
        auto_comment_thread = threading.Thread(
            target=_process_auto_comment_reply,
            args=(comment_id, comment_text, post_caption, user_id, username, post_id)
        )
        auto_comment_thread.daemon = True
        auto_comment_thread.start()
        
        # 2. Comment-to-DM Trigger
        comment_dm_thread = threading.Thread(
            target=_process_comment_to_dm,
            args=(comment_text, user_id, username, post_id, post_caption, comment_id)
        )
        comment_dm_thread.daemon = True
        comment_dm_thread.start()
        
        results['auto_comment_processed'] = True
        results['comment_to_dm_processed'] = True
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        current_app.logger.info(f'Comment automation dispatched in {elapsed_ms}ms')
        
    except Exception as e:
        current_app.logger.error(f'Comment event handling error: {e}')
        results['errors'].append(str(e))
    
    return results


def _process_auto_comment_reply(comment_id, comment_text, post_caption, user_id, username, post_id):
    """Process auto-reply to comment using RAG"""
    start_time = time.time()
    
    try:
        # Check if auto-comment is enabled
        settings = AutoReplySettings.query.filter_by(platform='instagram', is_active=True).first()
        
        if not settings:
            current_app.logger.debug('Auto-comment reply not enabled')
            return
        
        # Check ignore keywords
        if settings.ignore_keywords:
            ignore_list = json.loads(settings.ignore_keywords)
            comment_lower = comment_text.lower()
            if any(keyword.lower() in comment_lower for keyword in ignore_list):
                _log_automation('auto_comment_reply', 'skipped', False, 
                               f'Ignored due to keyword match', None, user_id, post_id, comment_id)
                return
        
        # Check rate limit
        from datetime import timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_replies = AutomationLog.query.filter(
            AutomationLog.automation_type == 'auto_comment_reply',
            AutomationLog.created_at >= one_hour_ago,
            AutomationLog.success == True
        ).count()
        
        if recent_replies >= settings.max_replies_per_hour:
            _log_automation('auto_comment_reply', 'rate_limited', False,
                           f'Rate limit exceeded ({recent_replies}/{settings.max_replies_per_hour})',
                           None, user_id, post_id, comment_id)
            return
        
        # Delay if configured (humanize)
        if settings.delay_seconds > 0:
            time.sleep(settings.delay_seconds)
        
        # Generate reply
        reply_text = None
        
        if settings.use_rag:
            # Use RAG for context-aware reply
            try:
                context = f"Post Caption: {post_caption}\n\nUser Comment: {comment_text}"
                prompt = f"""Generate a brief, {settings.tone} reply to this comment on our Instagram post. 
                
{context}

Reply as the brand/page owner. Keep it short (under 100 characters), engaging, and appropriate. 
Do not mention that you're an AI. Be natural and conversational."""
                
                rag_response = query_rag_system(prompt)
                
                if rag_response and rag_response.get('success'):
                    reply_text = rag_response.get('response', '').strip()
                    # Truncate if too long
                    if len(reply_text) > 150:
                        reply_text = reply_text[:147] + '...'
            except Exception as rag_error:
                current_app.logger.error(f'RAG generation failed: {rag_error}')
                reply_text = settings.fallback_message
        else:
            reply_text = settings.fallback_message
        
        if not reply_text:
            reply_text = settings.fallback_message
        
        # Post reply to comment (placeholder - implement actual API call)
        success = _post_comment_reply(comment_id, reply_text)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        _log_automation('auto_comment_reply', 
                       'replied_to_comment' if success else 'failed_to_reply',
                       success, 
                       None if success else 'API call failed',
                       reply_text, user_id, post_id, comment_id, elapsed_ms)
        
    except Exception as e:
        current_app.logger.error(f'Auto-comment reply error: {e}')
        _log_automation('auto_comment_reply', 'error', False, str(e), None, user_id, post_id, comment_id)


def _process_comment_to_dm(comment_text, user_id, username, post_id, post_caption, comment_id):
    """Process comment-to-DM triggers"""
    start_time = time.time()
    
    try:
        # Check for keyword matches
        comment_upper = comment_text.upper()
        
        matched_triggers = CommentTrigger.query.filter(
            CommentTrigger.is_active == True
        ).all()
        
        matched_trigger = None
        for trigger in matched_triggers:
            if trigger.keyword.upper() in comment_upper:
                matched_trigger = trigger
                break
        
        if not matched_trigger:
            current_app.logger.debug('No trigger keyword matched')
            return
        
        # Check if we already sent DM to this user for this post (loop hole protection)
        existing_dm = CommentDMTracker.query.filter_by(
            post_id=post_id,
            user_id=user_id
        ).first()
        
        if existing_dm:
            current_app.logger.info(f'DM already sent to {user_id} for post {post_id}')
            _log_automation('comment_to_dm', 'duplicate_prevented', True,
                           'DM already sent to this user for this post',
                           None, user_id, post_id, comment_id)
            return
        
        # Generate DM message
        dm_message = None
        
        if matched_trigger.use_rag:
            # Use RAG for dynamic response
            try:
                context = f"Post Caption: {post_caption}\n\nUser Comment: {comment_text}"
                prompt = f"""Generate a friendly DM message to send to {username} who commented on our post. 
                
{context}

They triggered the keyword: {matched_trigger.keyword}

Create a personalized message that:
1. Thanks them for commenting
2. Provides value related to their interest
3. Is conversational and under 200 characters

Do not mention that you're an AI."""
                
                rag_response = query_rag_system(prompt)
                
                if rag_response and rag_response.get('success'):
                    dm_message = rag_response.get('response', '').strip()
            except Exception as rag_error:
                current_app.logger.error(f'RAG DM generation failed: {rag_error}')
                dm_message = matched_trigger.dm_response
        else:
            dm_message = matched_trigger.dm_response
        
        if not dm_message:
            dm_message = "Thanks for your comment! 🙏"
        
        # Send DM
        dm_result = send_instagram_message(user_id, dm_message)
        
        if dm_result.get('success'):
            # Record that we sent this DM
            tracker = CommentDMTracker(
                post_id=post_id,
                user_id=user_id,
                trigger_keyword=matched_trigger.keyword
            )
            db.session.add(tracker)
            
            # Update trigger stats
            matched_trigger.times_triggered += 1
            
            db.session.commit()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            _log_automation('comment_to_dm', 'sent_dm', True, None,
                           dm_message, user_id, post_id, comment_id, elapsed_ms)
        else:
            _log_automation('comment_to_dm', 'failed_to_send', False,
                           dm_result.get('error'), dm_message, user_id, post_id, comment_id)
        
    except Exception as e:
        current_app.logger.error(f'Comment-to-DM error: {e}')
        _log_automation('comment_to_dm', 'error', False, str(e), None, user_id, post_id, comment_id)


def _post_comment_reply(comment_id, reply_text):
    """
    Post a reply to an Instagram comment using the Graph API
    
    Args:
        comment_id: Instagram comment ID
        reply_text: Reply message text
    
    Returns:
        dict: API response with comment ID, or None on failure
    """
    try:
        access_token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
        if not access_token:
            current_app.logger.error('INSTAGRAM_ACCESS_TOKEN not configured')
            return None
            
        url = f'https://graph.facebook.com/v19.0/{comment_id}/replies'
        
        payload = {
            'message': reply_text,
            'access_token': access_token
        }
        
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        current_app.logger.info(f'Successfully posted reply to comment {comment_id}')
        return result
        
    except requests.RequestException as e:
        current_app.logger.error(f'Failed to post comment reply to {comment_id}: {e}')
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                current_app.logger.error(f'Instagram API error: {error_data}')
            except:
                current_app.logger.error(f'Response text: {e.response.text}')
        return None
    except Exception as e:
        current_app.logger.error(f'Unexpected error posting comment reply: {e}')
        return None


def _log_automation(automation_type, action_taken, success, error_message, 
                   response_text, user_id, post_id, comment_id, response_time_ms=None):
    """Log automation activity to database"""
    try:
        log = AutomationLog(
            automation_type=automation_type,
            platform='instagram',
            action_taken=action_taken,
            success=success,
            error_message=error_message,
            response_text=response_text,
            user_id=user_id,
            post_id=post_id,
            comment_id=comment_id,
            response_time_ms=response_time_ms
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f'Failed to log automation: {e}')
