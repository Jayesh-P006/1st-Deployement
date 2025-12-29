"""
Gemini Vision Service for analyzing images and generating content
"""
import google.generativeai as genai
from flask import current_app
import PIL.Image
import os

def initialize_vision_model():
    """Initialize Gemini Vision model"""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError('GEMINI_API_KEY not configured')
    
    genai.configure(api_key=api_key)
    # Use gemini-2.5-flash for vision capabilities
    return genai.GenerativeModel('gemini-2.5-flash')

def generate_fallback_caption(platform='instagram', draft_title=''):
    """Generate a template caption when Gemini API is unavailable"""
    if platform == 'instagram':
        templates = [
            f"✨ {draft_title}\n\nSwipe to see more! 📸",
            f"🎯 {draft_title}\n\nDouble tap if you agree! 💫",
            f"📢 {draft_title}\n\nTag someone who needs to see this! 👇",
            f"💡 {draft_title}\n\nThoughts? Drop a comment below! 💬"
        ]
    else:  # LinkedIn
        templates = [
            f"🔔 {draft_title}\n\nLet's discuss in the comments.",
            f"💼 {draft_title}\n\nShare your thoughts below.",
            f"🎯 {draft_title}\n\nWhat's your take on this?",
            f"📊 {draft_title}\n\nInsights welcome in the comments."
        ]
    
    import random
    return random.choice(templates)

def analyze_image_for_caption(image_path, platform='instagram', draft_title=''):
    """
    Analyze image and generate engaging social media caption
    
    Args:
        image_path: Path to the image file
        platform: Social media platform (instagram/linkedin)
        draft_title: Title of the draft for context
        
    Returns:
        dict: {'success': bool, 'caption': str, 'error': str, 'is_fallback': bool}
    """
    try:
        model = initialize_vision_model()
        
        # Open and prepare image
        img = PIL.Image.open(image_path)
        
        # Build platform-specific prompt
        if platform == 'instagram':
            prompt = f"""Analyze this image and generate an engaging Instagram caption.

Context: This is for a post titled "{draft_title}"

Requirements:
- Write 2-3 sentences that are catchy and authentic
- Include relevant emojis naturally
- Make it conversational and relatable
- Focus on the visual elements in the image
- Keep it under 150 characters for better engagement
- Don't use hashtags (we'll add them separately)

Generate ONLY the caption text, nothing else."""

        else:  # LinkedIn
            prompt = f"""Analyze this image and generate a professional LinkedIn post caption.

Context: This is for a post titled "{draft_title}"

Requirements:
- Write 2-3 professional but engaging sentences
- Use minimal emojis (1-2 max)
- Focus on value, insights, or professional context
- Keep tone authentic but polished
- Highlight what's visible in the image
- Keep it concise (under 200 characters)

Generate ONLY the caption text, nothing else."""
        
        # Generate content
        response = model.generate_content([prompt, img])
        
        if response.text:
            caption = response.text.strip()
            return {
                'success': True,
                'caption': caption,
                'error': None
            }
        else:
            return {
                'success': False,
                'caption': None,
                'error': 'No content generated'
            }
            
    except Exception as e:
        error_str = str(e)
        current_app.logger.error(f'Vision analysis error: {e}')
        
        # Check if it's a quota error
        if '429' in error_str or 'quota' in error_str.lower() or 'rate limit' in error_str.lower():
            # Use fallback caption
            fallback_caption = generate_fallback_caption(platform, draft_title)
            return {
                'success': True,
                'caption': fallback_caption,
                'error': None,
                'is_fallback': True,
                'warning': 'AI quota exceeded. Generated a template caption. Please customize it.'
            }
        
        # For other errors, return fallback with error message
        fallback_caption = generate_fallback_caption(platform, draft_title)
        return {
            'success': True,
            'caption': fallback_caption,
            'error': None,
            'is_fallback': True,
            'warning': f'AI temporarily unavailable. Generated a template caption. Please customize it.'
        }

def analyze_multiple_images(image_paths, platform='instagram', draft_title=''):
    """
    Analyze multiple images and generate a cohesive caption
    
    Args:
        image_paths: List of image file paths
        platform: Social media platform
        draft_title: Title of the draft
        
    Returns:
        dict: {'success': bool, 'caption': str, 'error': str, 'is_fallback': bool}
    """
    try:
        model = initialize_vision_model()
        
        # Open all images
        images = [PIL.Image.open(path) for path in image_paths[:5]]  # Limit to 5 images
        
        if platform == 'instagram':
            prompt = f"""Analyze these {len(images)} images for an Instagram carousel post titled "{draft_title}".

Requirements:
- Write ONE cohesive caption that works for all images
- Mention that this is a multi-image post if relevant
- Keep it engaging and authentic (2-3 sentences)
- Use emojis naturally
- Under 150 characters
- No hashtags

Generate ONLY the caption text."""

        else:  # LinkedIn
            prompt = f"""Analyze these {len(images)} images for a LinkedIn post titled "{draft_title}".

Requirements:
- Write ONE professional caption that ties all images together
- Keep it polished but authentic (2-3 sentences)
- Minimal emojis (1-2 max)
- Under 200 characters

Generate ONLY the caption text."""
        
        # Generate content with all images
        content_parts = [prompt] + images
        response = model.generate_content(content_parts)
        
        if response.text:
            return {
                'success': True,
                'caption': response.text.strip(),
                'error': None
            }
        else:
            return {
                'success': False,
                'caption': None,
                'error': 'No content generated'
            }
            
    except Exception as e:
        error_str = str(e)
        current_app.logger.error(f'Multi-image vision analysis error: {e}')
        
        # Check if it's a quota error
        if '429' in error_str or 'quota' in error_str.lower() or 'rate limit' in error_str.lower():
            # Use fallback caption
            fallback_caption = generate_fallback_caption(platform, draft_title)
            return {
                'success': True,
                'caption': fallback_caption,
                'error': None,
                'is_fallback': True,
                'warning': 'AI quota exceeded. Generated a template caption. Please customize it.'
            }
        
        # For other errors, return fallback
        fallback_caption = generate_fallback_caption(platform, draft_title)
        return {
            'success': True,
            'caption': fallback_caption,
            'error': None,
            'is_fallback': True,
            'warning': 'AI temporarily unavailable. Generated a template caption. Please customize it.'
        }

def suggest_hashtags(caption, platform='instagram', max_tags=10):
    """
    Generate relevant hashtags based on caption content
    
    Args:
        caption: The post caption
        platform: Social media platform
        max_tags: Maximum number of hashtags
        
    Returns:
        list: List of hashtag strings (without #)
    """
    try:
        model = initialize_vision_model()
        
        prompt = f"""Based on this {platform} caption, suggest {max_tags} relevant hashtags.

Caption: "{caption}"

Requirements:
- Generate hashtags that are popular and relevant
- Mix of broad and niche tags
- No spaces in hashtags
- Return ONLY the hashtags, one per line
- Don't include the # symbol

Example format:
photography
travel
adventure"""

        response = model.generate_content(prompt)
        
        if response.text:
            hashtags = [tag.strip().replace('#', '') for tag in response.text.split('\n') if tag.strip()]
            return hashtags[:max_tags]
        else:
            return []
            
    except Exception as e:
        current_app.logger.error(f'Hashtag generation error: {e}')
        return []
