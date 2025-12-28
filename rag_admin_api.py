"""
RAG System Admin Dashboard API
===============================

Simple REST API endpoints to monitor and manage your RAG system.
Add these routes to your Flask app for easy monitoring.

Usage:
    # Add to your main app initialization
    from rag_admin_api import rag_admin_bp
    app.register_blueprint(rag_admin_bp, url_prefix='/api/rag-admin')

Then access:
    GET  /api/rag-admin/status        - System health check
    GET  /api/rag-admin/stats          - Detailed statistics
    POST /api/rag-admin/test           - Test chat response
    POST /api/rag-admin/ingest         - Manually ingest a post
    GET  /api/rag-admin/gatekeeper     - View gatekeeper patterns
    POST /api/rag-admin/clear-memory   - Clear conversation memory
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprint
rag_admin_bp = Blueprint('rag_admin', __name__)


@rag_admin_bp.route('/status', methods=['GET'])
def system_status():
    """
    Get RAG system health status.
    
    Returns:
        {
            "status": "healthy|degraded|error",
            "components": {
                "pinecone": "ok|error",
                "groq": "ok|error",
                "gemini": "ok|error"
            },
            "timestamp": "ISO timestamp"
        }
    """
    status = {
        "status": "healthy",
        "components": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check Pinecone
    try:
        from pinecone import Pinecone
        from config import Config
        
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        indexes = [idx.name for idx in pc.list_indexes()]
        
        if Config.PINECONE_INDEX_NAME in indexes:
            status["components"]["pinecone"] = "ok"
        else:
            status["components"]["pinecone"] = "index_not_found"
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["pinecone"] = f"error: {str(e)}"
        status["status"] = "error"
    
    # Check Groq
    try:
        from langchain_groq import ChatGroq
        from config import Config
        
        llm = ChatGroq(
            model=Config.GROQ_MODEL,
            groq_api_key=Config.GROQ_API_KEY,
            max_tokens=10
        )
        
        response = llm.invoke("Hi")
        status["components"]["groq"] = "ok"
    except Exception as e:
        status["components"]["groq"] = f"error: {str(e)}"
        status["status"] = "error"
    
    # Check Gemini
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from config import Config
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model=Config.GEMINI_EMBEDDING_MODEL,
            google_api_key=Config.GEMINI_API_KEY
        )
        
        test_embedding = embeddings.embed_query("test")
        status["components"]["gemini"] = "ok"
    except Exception as e:
        status["components"]["gemini"] = f"error: {str(e)}"
        status["status"] = "error"
    
    return jsonify(status)


@rag_admin_bp.route('/stats', methods=['GET'])
def system_stats():
    """
    Get detailed RAG system statistics.
    
    Returns comprehensive stats about posts, vectors, and usage.
    """
    from config import Config
    
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {},
        "pinecone": {},
        "configuration": {}
    }
    
    # Database stats (if available)
    try:
        from app.models import Post
        
        total_posts = Post.query.filter(Post.status == 'published').count()
        ingested_posts = Post.query.filter(Post.rag_ingested == True).count()
        pending_posts = Post.query.filter(
            Post.status == 'published',
            (Post.rag_ingested == False) | (Post.rag_ingested == None)
        ).count()
        
        stats["database"] = {
            "total_published_posts": total_posts,
            "ingested_posts": ingested_posts,
            "pending_ingestion": pending_posts,
            "ingestion_rate": f"{(ingested_posts/total_posts*100):.1f}%" if total_posts > 0 else "0%"
        }
    except Exception as e:
        stats["database"] = {"error": str(e)}
    
    # Pinecone stats
    try:
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        index = pc.Index(Config.PINECONE_INDEX_NAME)
        index_stats = index.describe_index_stats()
        
        stats["pinecone"] = {
            "index_name": Config.PINECONE_INDEX_NAME,
            "total_vectors": index_stats.get('total_vector_count', 0),
            "dimension": index_stats.get('dimension', 0),
            "environment": Config.PINECONE_ENVIRONMENT
        }
    except Exception as e:
        stats["pinecone"] = {"error": str(e)}
    
    # Configuration
    stats["configuration"] = {
        "retrieval_k": Config.RAG_RETRIEVAL_K,
        "max_context_tokens": Config.RAG_MAX_CONTEXT_TOKENS,
        "rate_limit_delay": Config.RAG_RATE_LIMIT_DELAY,
        "groq_model": Config.GROQ_MODEL,
        "gemini_vision_model": Config.GEMINI_VISION_MODEL,
        "gemini_embedding_model": Config.GEMINI_EMBEDDING_MODEL
    }
    
    return jsonify(stats)


@rag_admin_bp.route('/test', methods=['POST'])
def test_chat():
    """
    Test the chat system with a custom query.
    
    Request body:
        {
            "message": "When is the next event?",
            "conversation_id": "test_conv_123"  // optional
        }
    
    Returns:
        {
            "query": "When is the next event?",
            "response": "The next event is...",
            "metadata": {
                "source": "rag_llm|gatekeeper|error_fallback",
                "tokens_used": "0|estimated_50-200",
                "processing_time_ms": 1234,
                ...
            }
        }
    """
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400
    
    message = data['message']
    conversation_id = data.get('conversation_id', 'test_conversation')
    
    try:
        from app.ai.rag_chat import get_chat_pipeline
        
        pipeline = get_chat_pipeline()
        response, metadata = pipeline.generate_response(message, conversation_id)
        
        return jsonify({
            "query": message,
            "response": response,
            "metadata": metadata
        })
    
    except Exception as e:
        logger.error(f"Test chat failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@rag_admin_bp.route('/ingest', methods=['POST'])
def manual_ingest():
    """
    Manually ingest a post into the RAG system.
    
    Request body:
        {
            "post_id": "123",
            "image_url": "https://example.com/image.jpg",
            "caption": "Join our event!",
            "platform": "instagram"  // optional
        }
    
    Returns:
        {
            "success": true|false,
            "message": "Post ingested successfully"
        }
    """
    data = request.json
    
    required_fields = ['post_id', 'image_url', 'caption']
    if not all(field in data for field in required_fields):
        return jsonify({
            "error": f"Missing required fields: {required_fields}"
        }), 400
    
    try:
        from app.ai.rag_ingest import ingest_scheduled_post
        
        success = ingest_scheduled_post(
            post_id=data['post_id'],
            image_url=data['image_url'],
            caption=data['caption'],
            platform=data.get('platform', 'instagram')
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Post {data['post_id']} ingested successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Ingestion failed - check logs for details"
            }), 500
    
    except Exception as e:
        logger.error(f"Manual ingestion failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@rag_admin_bp.route('/gatekeeper', methods=['GET'])
def gatekeeper_info():
    """
    Get information about gatekeeper patterns and statistics.
    
    Returns:
        {
            "patterns": ["^hi+$", "^hello+$", ...],
            "static_responses": ["Hey! Thanks...", ...],
            "stats": {
                "total_responses_given": 123
            }
        }
    """
    try:
        from app.ai.rag_chat import get_chat_pipeline
        
        pipeline = get_chat_pipeline()
        gatekeeper = pipeline.gatekeeper
        
        return jsonify({
            "patterns": gatekeeper.GREETING_PATTERNS,
            "static_responses": gatekeeper.STATIC_RESPONSES,
            "stats": {
                "total_responses_given": gatekeeper.response_index,
                "current_response_index": gatekeeper.response_index % len(gatekeeper.STATIC_RESPONSES)
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rag_admin_bp.route('/clear-memory', methods=['POST'])
def clear_memory():
    """
    Clear the conversation memory buffer.
    
    This can help if:
    - Token usage is getting too high
    - Conversations are getting confused
    - You want to reset the context
    
    Returns:
        {
            "success": true,
            "message": "Conversation memory cleared"
        }
    """
    try:
        from app.ai.rag_chat import get_chat_pipeline
        
        pipeline = get_chat_pipeline()
        pipeline.clear_conversation_memory()
        
        logger.info("Conversation memory cleared via admin API")
        
        return jsonify({
            "success": True,
            "message": "Conversation memory cleared successfully"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rag_admin_bp.route('/rate-limiter', methods=['GET'])
def rate_limiter_stats():
    """
    Get rate limiter statistics.
    
    Returns:
        {
            "total_api_calls": 123,
            "delay_seconds": 2.0,
            "max_requests_per_minute": 30,
            "last_call_time": "ISO timestamp"
        }
    """
    try:
        from app.ai.rag_chat import get_chat_pipeline
        from config import Config
        import time
        
        pipeline = get_chat_pipeline()
        rate_limiter = pipeline.rate_limiter
        
        return jsonify({
            "total_api_calls": rate_limiter.call_count,
            "delay_seconds": rate_limiter.delay,
            "max_requests_per_minute": int(60 / rate_limiter.delay),
            "last_call_time": datetime.fromtimestamp(rate_limiter.last_call_time).isoformat() if rate_limiter.last_call_time > 0 else None,
            "groq_free_tier_limit": "30 req/min, 14,400 req/day"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rag_admin_bp.route('/test-batch', methods=['POST'])
def test_batch():
    """
    Test multiple queries in batch.
    
    Request body:
        {
            "queries": [
                "Hi there!",
                "When is the next event?",
                "Thanks!"
            ]
        }
    
    Returns:
        {
            "results": [
                {
                    "query": "Hi there!",
                    "response": "Hey! Thanks for reaching out!",
                    "metadata": {...}
                },
                ...
            ],
            "summary": {
                "total_queries": 3,
                "gatekeeper_hits": 2,
                "rag_hits": 1,
                "total_estimated_tokens": "50-200"
            }
        }
    """
    data = request.json
    
    if not data or 'queries' not in data:
        return jsonify({"error": "Missing 'queries' array in request body"}), 400
    
    queries = data['queries']
    
    if not isinstance(queries, list):
        return jsonify({"error": "'queries' must be an array"}), 400
    
    try:
        from app.ai.rag_chat import get_chat_pipeline
        
        pipeline = get_chat_pipeline()
        
        results = []
        gatekeeper_hits = 0
        rag_hits = 0
        
        for query in queries:
            response, metadata = pipeline.generate_response(query)
            
            results.append({
                "query": query,
                "response": response,
                "metadata": metadata
            })
            
            if metadata['source'] == 'gatekeeper':
                gatekeeper_hits += 1
            elif metadata['source'] == 'rag_llm':
                rag_hits += 1
        
        return jsonify({
            "results": results,
            "summary": {
                "total_queries": len(queries),
                "gatekeeper_hits": gatekeeper_hits,
                "rag_hits": rag_hits,
                "token_efficiency": f"{(gatekeeper_hits/len(queries)*100):.1f}% queries used 0 tokens"
            }
        })
    
    except Exception as e:
        logger.error(f"Batch test failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# How to Use This API
# ============================================================
"""
Add to your main Flask app (__init__.py or run.py):

    from rag_admin_api import rag_admin_bp
    app.register_blueprint(rag_admin_bp, url_prefix='/api/rag-admin')

Then access via:

    # Check system health
    GET http://your-app.com/api/rag-admin/status

    # Get detailed stats
    GET http://your-app.com/api/rag-admin/stats

    # Test a query
    POST http://your-app.com/api/rag-admin/test
    Body: {"message": "When is the next event?"}

    # Manually ingest a post
    POST http://your-app.com/api/rag-admin/ingest
    Body: {
        "post_id": "123",
        "image_url": "https://example.com/image.jpg",
        "caption": "Event caption"
    }

    # View gatekeeper patterns
    GET http://your-app.com/api/rag-admin/gatekeeper

    # Clear conversation memory
    POST http://your-app.com/api/rag-admin/clear-memory

    # Rate limiter stats
    GET http://your-app.com/api/rag-admin/rate-limiter

    # Test batch queries
    POST http://your-app.com/api/rag-admin/test-batch
    Body: {"queries": ["Hi!", "When is the event?"]}

IMPORTANT: In production, add authentication to these endpoints!
"""
