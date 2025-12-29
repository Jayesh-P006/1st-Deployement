"""
Gemini AI Service for generating personalized DM replies
"""
import google.generativeai as genai
from flask import current_app
import json
import time
from datetime import datetime

def initialize_gemini():
    """Initialize Gemini API with key from config"""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError('GEMINI_API_KEY not configured. Please set it in config.py or .env file')
    genai.configure(api_key=api_key)
    model_name = current_app.config.get('GEMINI_MODEL', 'gemini-2.5-flash')
    return genai.GenerativeModel(model_name)

def get_training_context():
    """Fetch all active training data to provide context to Gemini"""
    from ..models import TrainingData
    
    training_data = TrainingData.query.filter_by(is_active=True).order_by(TrainingData.priority.desc()).all()
    
    if not training_data:
        return "No specific training data available."
    
    context_parts = []
    
    # Organize by category
    categories = {}
    for data in training_data:
        if data.category not in categories:
            categories[data.category] = []
        categories[data.category].append(data)
    
    # Build context string
    for category, items in categories.items():
        context_parts.append(f"\n## {category.upper()} INFORMATION ##")
        for item in items:
            context_parts.append(f"\n### {item.title} ###")
            context_parts.append(item.content)
            
            if item.event_date:
                context_parts.append(f"Date: {item.event_date.strftime('%Y-%m-%d %H:%M')}")
            if item.location:
                context_parts.append(f"Location: {item.location}")
            if item.contact_info:
                context_parts.append(f"Contact: {item.contact_info}")
            
            if item.tags:
                try:
                    tags = json.loads(item.tags)
                    context_parts.append(f"Tags: {', '.join(tags)}")
                except:
                    pass
    
    return "\n".join(context_parts)

def get_conversation_history(conversation):
    """Get recent message history from conversation"""
    from ..models import DMMessage
    
    recent_messages = conversation.messages.order_by(DMMessage.created_at.desc()).limit(10).all()
    recent_messages.reverse()  # Chronological order
    
    history = []
    for msg in recent_messages:
        role = "user" if msg.sender_type == 'user' else "assistant"
        history.append({"role": role, "content": msg.message_text})
    
    return history

def build_system_prompt():
    """Build the system prompt with training data context"""
    training_context = get_training_context()
    
    system_prompt = f"""You are a helpful, friendly, and professional AI assistant representing a social media account. Your role is to respond to Instagram direct messages in a personalized, conversational way.

## YOUR GUIDELINES ##
1. Be warm, friendly, and professional
2. Keep responses concise (2-3 sentences unless more detail is needed)
3. Use the information provided below to answer questions accurately
4. If you don't know something, politely say so and offer to help with what you do know
5. Match the tone of the user (formal if they're formal, casual if they're casual)
6. Never make up information not provided in the context
7. Always aim to be helpful and guide users to the information they need

## AVAILABLE INFORMATION ##
{training_context}

## YOUR TASK ##
Based on the conversation history and the user's latest message, generate a helpful, personalized response that:
- Addresses their question or comment directly
- Uses relevant information from the context above
- Maintains a natural, conversational tone
- Encourages further engagement when appropriate
"""
    
    return system_prompt

def generate_reply(conversation, user_message):
    """
    Generate a personalized reply using Gemini AI
    
    Args:
        conversation: DMConversation object
        user_message: The latest message text from the user
    
    Returns:
        dict: {
            'reply': str (generated reply text),
            'prompt': str (full prompt used),
            'response_time': float (time taken),
            'success': bool,
            'error': str (if any)
        }
    """
    start_time = time.time()
    
    try:
        # Initialize Gemini
        model = initialize_gemini()
        
        # Build system prompt with training context
        system_prompt = build_system_prompt()
        
        # Get conversation history
        history = get_conversation_history(conversation)
        
        # Build the full prompt
        conversation_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
        
        full_prompt = f"""{system_prompt}

## CONVERSATION HISTORY ##
{conversation_text}
USER: {user_message}

## YOUR RESPONSE ##
Generate a helpful reply to the user's latest message above:"""
        
        # Generate response
        response = model.generate_content(full_prompt)
        reply_text = response.text.strip()
        
        response_time = time.time() - start_time
        
        return {
            'reply': reply_text,
            'prompt': full_prompt,
            'response_time': response_time,
            'success': True,
            'error': None
        }
    
    except Exception as e:
        response_time = time.time() - start_time
        return {
            'reply': None,
            'prompt': None,
            'response_time': response_time,
            'success': False,
            'error': str(e)
        }

def generate_greeting(username=None):
    """Generate a welcoming greeting message"""
    from ..models import ChatSettings
    
    settings = ChatSettings.query.first()
    if settings and settings.default_greeting:
        greeting = settings.default_greeting
        if username:
            greeting = f"Hi {username}! {greeting}"
        return greeting
    
    if username:
        return f"Hi {username}! Thanks for reaching out. How can I help you today?"
    return "Hello! Thanks for reaching out. How can I help you today?"

def generate_fallback_response():
    """Generate a fallback response when Gemini fails"""
    from ..models import ChatSettings
    
    settings = ChatSettings.query.first()
    if settings and settings.fallback_message:
        return settings.fallback_message
    
    return "I'm sorry, I'm having trouble processing that right now. Could you please try again or rephrase your message?"

def is_within_business_hours():
    """Check if current time is within business hours"""
    from ..models import ChatSettings
    
    settings = ChatSettings.query.first()
    if not settings or not settings.business_hours_only:
        return True
    
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    
    return settings.business_hours_start <= current_time <= settings.business_hours_end

def should_auto_reply(message_text, conversation):
    """
    Determine if we should auto-reply to this message
    
    Args:
        message_text: The incoming message text
        conversation: DMConversation object
    
    Returns:
        tuple: (should_reply: bool, reason: str)
    """
    from ..models import ChatSettings
    import json
    
    settings = ChatSettings.query.first()
    
    # Check if auto-reply is enabled
    if not settings or not settings.auto_reply_enabled:
        return False, "Auto-reply is disabled"
    
    # Check if message is too old (don't reply to messages older than 5 minutes)
    from datetime import datetime, timedelta
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    if conversation.last_message_at and conversation.last_message_at < five_minutes_ago:
        return False, "Message too old (> 5 minutes)"
    
    # Check business hours
    if not is_within_business_hours():
        return False, "Outside business hours"
    
    # Check rate limit (replies in last hour)
    from ..models import DMMessage
    from datetime import timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_auto_replies = DMMessage.query.filter(
        DMMessage.conversation_id == conversation.id,
        DMMessage.is_auto_reply == True,
        DMMessage.created_at >= one_hour_ago
    ).count()
    
    if recent_auto_replies >= settings.reply_rate_limit:
        return False, f"Rate limit reached ({settings.reply_rate_limit}/hour)"
    
    # Check blacklist keywords
    if settings.blacklist_keywords:
        try:
            blacklist = json.loads(settings.blacklist_keywords)
            message_lower = message_text.lower()
            for keyword in blacklist:
                if keyword.lower() in message_lower:
                    return False, f"Blacklisted keyword: {keyword}"
        except:
            pass
    
    return True, "OK"
