"""
RAG System Status & Management Routes
Monitor and manage the Hybrid RAG system for auto-replies
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
import json
from . import db
from .auth import login_required, get_current_user

rag_bp = Blueprint('rag', __name__, url_prefix='/rag')

@rag_bp.route('/')
@login_required
def status():
    """View RAG system status and statistics"""
    try:
        from .ai.rag_ingest import get_ingestion_pipeline
        from .ai.rag_chat import get_chat_pipeline
        
        # Get ingestion pipeline stats
        ingest_pipeline = get_ingestion_pipeline()
        
        # Get chat pipeline stats
        chat_pipeline = get_chat_pipeline()
        
        # Get Pinecone stats
        try:
            index_stats = chat_pipeline.vector_store._index.describe_index_stats()
            pinecone_stats = {
                'connected': True,
                'total_vectors': index_stats.get('total_vector_count', 0),
                'dimension': index_stats.get('dimension', 768),
                'index_name': chat_pipeline.vector_store._index_name,
            }
        except Exception as e:
            pinecone_stats = {
                'connected': False,
                'error': str(e)
            }
        
        # Get gatekeeper stats
        gatekeeper_stats = {
            'enabled': True,
            'pattern_count': len(chat_pipeline.gatekeeper.GREETING_PATTERNS),
            'estimated_efficiency': '60-80%'
        }
        
        # Get rate limiter stats
        rate_limiter_stats = {
            'enabled': True,
            'delay': chat_pipeline.rate_limiter.delay_seconds,
            'last_call': chat_pipeline.rate_limiter.last_call_time.strftime('%Y-%m-%d %H:%M:%S') if chat_pipeline.rate_limiter.last_call_time else 'Never'
        }
        
        # System configuration
        from config import Config
        system_config = {
            'groq_configured': bool(Config.GROQ_API_KEY and Config.GROQ_API_KEY != 'your_groq_api_key_here'),
            'pinecone_configured': bool(Config.PINECONE_API_KEY and Config.PINECONE_API_KEY != 'your_pinecone_api_key_here'),
            'gemini_configured': bool(Config.GEMINI_API_KEY),
            'retrieval_k': Config.RAG_RETRIEVAL_K,
            'max_context_tokens': Config.RAG_MAX_CONTEXT_TOKENS,
            'rate_limit_delay': Config.RAG_RATE_LIMIT_DELAY,
        }
        
        # Check if system is fully operational
        system_operational = (
            system_config['groq_configured'] and 
            system_config['pinecone_configured'] and 
            system_config['gemini_configured'] and
            pinecone_stats.get('connected', False)
        )
        
        return render_template('rag/status.html',
                             pinecone_stats=pinecone_stats,
                             gatekeeper_stats=gatekeeper_stats,
                             rate_limiter_stats=rate_limiter_stats,
                             system_config=system_config,
                             system_operational=system_operational)
    
    except Exception as e:
        flash(f'Error loading RAG system status: {str(e)}', 'danger')
        return render_template('rag/status.html',
                             pinecone_stats={'connected': False, 'error': str(e)},
                             gatekeeper_stats={},
                             rate_limiter_stats={},
                             system_config={},
                             system_operational=False)


@rag_bp.route('/test', methods=['POST'])
@login_required
def test_system():
    """Test the RAG system with a sample query"""
    query = request.form.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query is required'})
    
    try:
        from .ai.rag_chat import generate_dm_response
        
        # Generate response
        start_time = datetime.now()
        response = generate_dm_response(
            message=query,
            conversation_id='test_user'
        )
        end_time = datetime.now()
        
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return jsonify({
            'success': True,
            'query': query,
            'response': response,
            'duration_ms': round(duration_ms, 2)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@rag_bp.route('/ingest-post', methods=['POST'])
@login_required
def ingest_post():
    """Manually trigger ingestion for a specific post"""
    post_id = request.form.get('post_id', '').strip()
    
    if not post_id:
        return jsonify({'success': False, 'error': 'Post ID is required'})
    
    try:
        from .models import ScheduledPost
        from .ai.rag_ingest import get_ingestion_pipeline
        
        post = ScheduledPost.query.get_or_404(post_id)
        
        if not post.image_path:
            return jsonify({'success': False, 'error': 'Post has no image to ingest'})
        
        pipeline = get_ingestion_pipeline()
        success = pipeline.ingest_post(
            post_id=str(post.id),
            image_url=post.image_path,
            caption=post.caption or "",
            platform=post.platform,
            scheduled_time=post.scheduled_time
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Post {post_id} ingested successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ingestion failed (check logs for details)'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@rag_bp.route('/clear-memory', methods=['POST'])
@login_required
def clear_memory():
    """Clear conversation memory for a specific user"""
    conversation_id = request.form.get('conversation_id', 'test_user').strip()
    
    try:
        from .ai.rag_chat import get_chat_pipeline
        
        chat_pipeline = get_chat_pipeline()
        chat_pipeline.memory.clear()
        
        return jsonify({
            'success': True,
            'message': f'Memory cleared for conversation: {conversation_id}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@rag_bp.route('/stats')
@login_required
def stats():
    """View detailed RAG system statistics"""
    try:
        from .ai.rag_chat import get_chat_pipeline
        from .models import DMMessage, DMConversation
        
        chat_pipeline = get_chat_pipeline()
        
        # Get Pinecone detailed stats
        try:
            index = chat_pipeline.vector_store._index
            index_stats = index.describe_index_stats()
            
            pinecone_details = {
                'total_vectors': index_stats.get('total_vector_count', 0),
                'dimension': index_stats.get('dimension', 768),
                'index_fullness': index_stats.get('index_fullness', 0),
                'namespaces': index_stats.get('namespaces', {}),
            }
        except Exception as e:
            pinecone_details = {'error': str(e)}
        
        # Get DM statistics
        total_conversations = DMConversation.query.count()
        total_messages = DMMessage.query.count()
        bot_messages = DMMessage.query.filter_by(sender_type='bot').count()
        
        dm_stats = {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'bot_messages': bot_messages,
            'user_messages': total_messages - bot_messages,
        }
        
        return jsonify({
            'success': True,
            'pinecone': pinecone_details,
            'dm_stats': dm_stats,
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
