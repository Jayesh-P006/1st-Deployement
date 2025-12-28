"""
Example Integration: Automated Post Ingestion
==============================================

This file demonstrates how to integrate the RAG ingestion system into your
post scheduling and publishing workflow. Copy relevant sections to your
actual routes.py or publishing functions.

"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from config import Config
from app.models import db, Post
from app.ai.rag_ingest import ingest_scheduled_post

logger = logging.getLogger(__name__)

# Create blueprint
post_blueprint = Blueprint('post', __name__)


# ============================================================
# OPTION 1: Ingest When Post is Scheduled
# ============================================================

@post_blueprint.route('/api/schedule-post', methods=['POST'])
def schedule_post():
    """
    Schedule a new post and automatically ingest into RAG system.
    
    This approach ingests posts as soon as they're scheduled, which means:
    - Your RAG system learns immediately
    - Users get instant answers about upcoming events
    - Slightly more API calls (but still very cheap)
    """
    try:
        data = request.json
        
        # Extract post details
        caption = data.get('caption')
        image_url = data.get('image_url')
        platform = data.get('platform', 'instagram')
        scheduled_time = datetime.fromisoformat(data.get('scheduled_time'))
        
        # Validate required fields
        if not caption or not image_url:
            return jsonify({'error': 'Caption and image_url required'}), 400
        
        # Create post in database
        new_post = Post(
            caption=caption,
            image_url=image_url,
            platform=platform,
            scheduled_time=scheduled_time,
            status='scheduled',
            user_id=data.get('user_id')
        )
        db.session.add(new_post)
        db.session.commit()
        
        logger.info(f"Created post {new_post.id} for {scheduled_time}")
        
        # NEW: Automatically ingest into RAG system
        # TOKEN OPTIMIZATION: This happens in background, doesn't slow down API response
        try:
            success = ingest_scheduled_post(
                post_id=str(new_post.id),
                image_url=new_post.image_url,
                caption=new_post.caption,
                platform=new_post.platform,
                scheduled_time=new_post.scheduled_time
            )
            
            if success:
                logger.info(f"✓ Post {new_post.id} ingested into RAG system")
                new_post.rag_ingested = True  # Optional: Track ingestion status
                db.session.commit()
            else:
                logger.warning(f"✗ Failed to ingest post {new_post.id} into RAG")
                # Don't fail the entire request - post is still scheduled
        
        except Exception as e:
            logger.error(f"RAG ingestion error for post {new_post.id}: {str(e)}")
            # Don't fail the entire request - post is still scheduled
        
        return jsonify({
            'success': True,
            'post_id': new_post.id,
            'scheduled_time': new_post.scheduled_time.isoformat(),
            'rag_ingested': getattr(new_post, 'rag_ingested', False)
        }), 201
    
    except Exception as e:
        logger.error(f"Failed to schedule post: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================
# OPTION 2: Ingest When Post is Published
# ============================================================

def publish_post_to_instagram(post: Post) -> bool:
    """
    Publish a post to Instagram and ingest into RAG system.
    
    This approach ingests posts only after they're published, which means:
    - More accurate data (post is definitely live)
    - Slightly delayed learning (but still automatic)
    - Fewer wasted API calls if posts are cancelled
    
    Args:
        post: Post object from database
        
    Returns:
        True if successful, False otherwise
    """
    import requests
    
    try:
        # Step 1: Create Instagram container
        container_url = f"https://graph.facebook.com/v18.0/{Config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
        
        container_params = {
            'image_url': post.image_url,
            'caption': post.caption,
            'access_token': Config.INSTAGRAM_ACCESS_TOKEN
        }
        
        container_response = requests.post(container_url, params=container_params)
        container_response.raise_for_status()
        container_id = container_response.json()['id']
        
        logger.info(f"Created Instagram container: {container_id}")
        
        # Step 2: Publish the container
        publish_url = f"https://graph.facebook.com/v18.0/{Config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
        
        publish_params = {
            'creation_id': container_id,
            'access_token': Config.INSTAGRAM_ACCESS_TOKEN
        }
        
        publish_response = requests.post(publish_url, params=publish_params)
        publish_response.raise_for_status()
        media_id = publish_response.json()['id']
        
        logger.info(f"Published to Instagram: {media_id}")
        
        # Step 3: Update database
        post.status = 'published'
        post.instagram_media_id = media_id
        post.published_at = datetime.utcnow()
        db.session.commit()
        
        # Step 4: NEW - Ingest into RAG system
        # TOKEN OPTIMIZATION: Only ingest actually published posts
        try:
            success = ingest_scheduled_post(
                post_id=str(post.id),
                image_url=post.image_url,
                caption=post.caption,
                platform='instagram',
                scheduled_time=post.scheduled_time
            )
            
            if success:
                logger.info(f"✓ Published post {post.id} ingested into RAG system")
                post.rag_ingested = True
                db.session.commit()
            else:
                logger.warning(f"✗ Failed to ingest published post {post.id}")
        
        except Exception as e:
            logger.error(f"RAG ingestion error: {str(e)}")
            # Don't fail the publish - post is already live
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to publish post {post.id}: {str(e)}")
        post.status = 'failed'
        db.session.commit()
        return False


# ============================================================
# OPTION 3: Batch Ingestion (Background Job)
# ============================================================

def ingest_recent_posts_batch(hours: int = 24):
    """
    Batch ingest all posts from the last N hours.
    
    Use this as a scheduled job (e.g., via APScheduler) to:
    - Catch any posts that failed to ingest initially
    - Re-ingest updated posts
    - Backfill data periodically
    
    Args:
        hours: Number of hours to look back (default: 24)
    """
    from datetime import timedelta
    from app.ai.rag_ingest import get_ingestion_pipeline
    
    try:
        # Get posts from last N hours
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        posts_to_ingest = Post.query.filter(
            Post.status == 'published',
            Post.published_at >= cutoff_time,
            Post.image_url.isnot(None)
        ).all()
        
        if not posts_to_ingest:
            logger.info(f"No posts to ingest from last {hours} hours")
            return
        
        logger.info(f"Starting batch ingestion of {len(posts_to_ingest)} posts")
        
        # Prepare batch data
        pipeline = get_ingestion_pipeline()
        
        posts_data = [
            {
                'post_id': str(post.id),
                'image_url': post.image_url,
                'caption': post.caption or '',
                'platform': post.platform,
                'scheduled_time': post.scheduled_time
            }
            for post in posts_to_ingest
        ]
        
        # Batch ingest
        results = pipeline.batch_ingest_posts(posts_data)
        
        logger.info(
            f"Batch ingestion complete: "
            f"{results['success']} succeeded, {results['failed']} failed"
        )
        
        # Optional: Mark successfully ingested posts
        if results['success'] > 0:
            for post in posts_to_ingest:
                post.rag_ingested = True
            db.session.commit()
    
    except Exception as e:
        logger.error(f"Batch ingestion failed: {str(e)}")


# ============================================================
# Setup Scheduled Job (using APScheduler)
# ============================================================

def setup_rag_ingestion_jobs(scheduler):
    """
    Setup automated ingestion jobs.
    
    Add this to your run.py or __init__.py where you initialize APScheduler.
    
    Args:
        scheduler: APScheduler instance
    """
    
    # Job 1: Ingest recent posts every hour
    scheduler.add_job(
        func=ingest_recent_posts_batch,
        trigger='interval',
        hours=1,
        id='rag_hourly_ingest',
        name='RAG Hourly Post Ingestion',
        replace_existing=True
    )
    
    logger.info("RAG ingestion jobs scheduled")


# ============================================================
# Manual Ingestion Endpoints (Admin/Testing)
# ============================================================

@post_blueprint.route('/api/admin/ingest-post/<int:post_id>', methods=['POST'])
def manually_ingest_post(post_id: int):
    """
    Manually trigger ingestion for a specific post.
    
    Useful for:
    - Testing the ingestion pipeline
    - Re-ingesting updated posts
    - Fixing failed ingestions
    """
    try:
        post = Post.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        if not post.image_url:
            return jsonify({'error': 'Post has no image'}), 400
        
        # Ingest the post
        success = ingest_scheduled_post(
            post_id=str(post.id),
            image_url=post.image_url,
            caption=post.caption or '',
            platform=post.platform,
            scheduled_time=post.scheduled_time
        )
        
        if success:
            post.rag_ingested = True
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Post {post_id} ingested successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Ingestion failed - check logs'
            }), 500
    
    except Exception as e:
        logger.error(f"Manual ingestion failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@post_blueprint.route('/api/admin/batch-ingest', methods=['POST'])
def manually_batch_ingest():
    """
    Manually trigger batch ingestion.
    
    Request body:
    {
        "hours": 24,  // Optional: hours to look back (default: 24)
        "force_reingest": false  // Optional: re-ingest already ingested posts
    }
    """
    try:
        data = request.json or {}
        hours = data.get('hours', 24)
        force_reingest = data.get('force_reingest', False)
        
        from datetime import timedelta
        from app.ai.rag_ingest import get_ingestion_pipeline
        
        # Get posts
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = Post.query.filter(
            Post.status == 'published',
            Post.published_at >= cutoff_time,
            Post.image_url.isnot(None)
        )
        
        # Filter out already ingested posts unless force_reingest
        if not force_reingest:
            query = query.filter(
                (Post.rag_ingested == False) | (Post.rag_ingested == None)
            )
        
        posts = query.all()
        
        if not posts:
            return jsonify({
                'message': 'No posts to ingest',
                'count': 0
            })
        
        # Batch ingest
        pipeline = get_ingestion_pipeline()
        
        posts_data = [
            {
                'post_id': str(post.id),
                'image_url': post.image_url,
                'caption': post.caption or '',
                'platform': post.platform,
                'scheduled_time': post.scheduled_time
            }
            for post in posts
        ]
        
        results = pipeline.batch_ingest_posts(posts_data)
        
        # Update database
        for post in posts:
            post.rag_ingested = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'total_posts': len(posts),
            'succeeded': results['success'],
            'failed': results['failed']
        })
    
    except Exception as e:
        logger.error(f"Batch ingestion failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# RAG Status Endpoint
# ============================================================

@post_blueprint.route('/api/admin/rag-stats', methods=['GET'])
def rag_statistics():
    """
    Get RAG system statistics.
    
    Returns info about:
    - Total posts ingested
    - Posts pending ingestion
    - Recent ingestion activity
    """
    try:
        total_posts = Post.query.filter(Post.status == 'published').count()
        ingested_posts = Post.query.filter(Post.rag_ingested == True).count()
        pending_posts = Post.query.filter(
            Post.status == 'published',
            (Post.rag_ingested == False) | (Post.rag_ingested == None)
        ).count()
        
        # Optional: Get Pinecone stats
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=Config.PINECONE_API_KEY)
            index = pc.Index(Config.PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()
            vector_count = stats.get('total_vector_count', 0)
        except Exception:
            vector_count = 'unavailable'
        
        return jsonify({
            'database_stats': {
                'total_published_posts': total_posts,
                'ingested_posts': ingested_posts,
                'pending_ingestion': pending_posts,
                'ingestion_rate': f"{(ingested_posts/total_posts*100):.1f}%" if total_posts > 0 else "0%"
            },
            'pinecone_stats': {
                'total_vectors': vector_count,
                'index_name': Config.PINECONE_INDEX_NAME
            }
        })
    
    except Exception as e:
        logger.error(f"Failed to get RAG stats: {str(e)}")
        return jsonify({'error': str(e)}), 500
