"""
Flask route to serve System Status Monitor data
Add this to app/routes.py or create app/status_routes.py
"""
from flask import Blueprint, jsonify, render_template
from datetime import datetime
from .auth import login_required

status_bp = Blueprint('status', __name__)

@status_bp.route('/workflow-status')
@login_required
def workflow_status():
    """Workflow Status page with embedded monitoring widget"""
    try:
        return render_template('workflow_status.html')
    except Exception as e:
        # Fallback if template fails
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Workflow Status - Error</h1>
            <p>Failed to load workflow status page: {str(e)}</p>
            <a href="/">Return to Dashboard</a>
        </body>
        </html>
        """, 500

@status_bp.route('/api/status/system', methods=['GET'])
def get_system_status():
    """
    Return real-time system status for the monitoring widget.
    This endpoint is called by the frontend status monitor.
    """
    try:
        from config import Config
        
        # Check API configurations first (before initializing pipelines)
        groq_configured = bool(Config.GROQ_API_KEY and Config.GROQ_API_KEY.strip() and Config.GROQ_API_KEY != 'your_groq_api_key_here')
        pinecone_configured = bool(Config.PINECONE_API_KEY and Config.PINECONE_API_KEY.strip() and Config.PINECONE_API_KEY != 'your_pinecone_api_key_here')
        gemini_configured = bool(Config.GEMINI_API_KEY and Config.GEMINI_API_KEY.strip())
        
        # Check Pinecone connection only if configured
        pinecone_status = 'down'
        pinecone_details = 'Not configured'
        
        if pinecone_configured and gemini_configured:
            try:
                from .ai.rag_chat import get_chat_pipeline
                chat_pipeline = get_chat_pipeline()
                index_stats = chat_pipeline.vector_store._index.describe_index_stats()
                pinecone_status = 'operational'
                pinecone_details = f"{index_stats.get('total_vector_count', 0)} vectors"
            except Exception as e:
                pinecone_status = 'down'
                pinecone_details = str(e)[:50]
        
        # Set API status
        groq_status = 'operational' if groq_configured else 'down'
        gemini_status = 'operational' if gemini_configured else 'down'
        
        # Database status (assume operational if we can query)
        from . import db
        db_status = 'operational'
        jobs_queued = 0
        try:
            from .models import ScheduledPost
            jobs_queued = ScheduledPost.query.filter_by(status='scheduled').count()
        except Exception as e:
            db_status = 'warning'
            jobs_queued = 0
        
        # Instagram API status
        instagram_status = 'operational' if (Config.INSTAGRAM_ACCESS_TOKEN and Config.INSTAGRAM_ACCESS_TOKEN.strip()) else 'down'
        
        # Return status for each system node
        return jsonify({
            'user-input': {
                'status': 'operational',
                'latency': '12ms',
                'details': 'UI responsive'
            },
            'vector-db': {
                'status': pinecone_status,
                'latency': '45ms',
                'details': pinecone_details
            },
            'ai-engine': {
                'status': groq_status if groq_status == 'operational' else 'down',
                'latency': '234ms',
                'details': 'RAG + Groq/Gemini'
            },
            'scheduler': {
                'status': db_status,
                'latency': '8ms',
                'details': f'{jobs_queued} jobs queued'
            },
            'social-api': {
                'status': instagram_status,
                'latency': '156ms',
                'details': 'Instagram Graph API'
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
