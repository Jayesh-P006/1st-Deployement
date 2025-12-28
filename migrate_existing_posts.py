"""
Migration Script: Ingest Existing Posts into RAG System
========================================================

This script migrates your existing published posts into the RAG vector database.
Run this ONCE after setting up the RAG system to backfill your knowledge base.

Usage:
    python migrate_existing_posts.py [options]

Options:
    --limit N       Only ingest first N posts (for testing)
    --force         Re-ingest posts even if already marked as ingested
    --platform P    Only ingest posts from specific platform (instagram/linkedin)
    --dry-run       Show what would be ingested without actually doing it

Examples:
    # Ingest all published posts
    python migrate_existing_posts.py

    # Test with first 10 posts
    python migrate_existing_posts.py --limit 10

    # Re-ingest all Instagram posts
    python migrate_existing_posts.py --platform instagram --force

    # Dry run to see what would be ingested
    python migrate_existing_posts.py --dry-run
"""

import sys
import argparse
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_posts(limit=None, force=False, platform=None, dry_run=False):
    """
    Migrate existing posts to RAG system.
    
    Args:
        limit: Maximum number of posts to migrate (None = all)
        force: Re-ingest posts even if already marked as ingested
        platform: Filter by platform ('instagram', 'linkedin', or None for all)
        dry_run: Show what would be done without actually doing it
    """
    # Import here to avoid errors if DB not initialized
    try:
        from app import db
        from app.models import Post
        from app.ai.rag_ingest import get_ingestion_pipeline
    except Exception as e:
        logger.error(f"Failed to import required modules: {str(e)}")
        logger.error("Make sure you're running this from the project root directory")
        return
    
    print("\n" + "="*60)
    print("RAG SYSTEM MIGRATION: Ingest Existing Posts")
    print("="*60 + "\n")
    
    # Build query
    query = Post.query.filter(
        Post.status == 'published',
        Post.image_url.isnot(None)
    )
    
    # Filter by platform if specified
    if platform:
        query = query.filter(Post.platform == platform)
        print(f"Filtering by platform: {platform}")
    
    # Filter out already ingested unless force=True
    if not force:
        query = query.filter(
            (Post.rag_ingested == False) | (Post.rag_ingested == None)
        )
        print("Filtering: Only posts not yet ingested")
    else:
        print("Force mode: Will re-ingest all posts")
    
    # Apply limit
    if limit:
        query = query.limit(limit)
        print(f"Limit: {limit} posts")
    
    # Get posts
    posts = query.all()
    
    if not posts:
        print("\n✓ No posts to migrate!")
        print("All your posts are already in the RAG system.")
        return
    
    print(f"\nFound {len(posts)} posts to ingest\n")
    
    # Dry run mode - just show what would be done
    if dry_run:
        print("DRY RUN MODE - No actual changes will be made\n")
        print("Posts that would be ingested:")
        print("-" * 60)
        
        for i, post in enumerate(posts, 1):
            print(f"\n[{i}/{len(posts)}] Post ID: {post.id}")
            print(f"  Platform: {post.platform}")
            print(f"  Caption: {post.caption[:60] if post.caption else 'No caption'}...")
            print(f"  Image: {post.image_url[:60]}...")
            print(f"  Published: {post.published_at or post.scheduled_time}")
        
        print("\n" + "-" * 60)
        print(f"\nTotal posts that would be ingested: {len(posts)}")
        print("\nTo actually ingest these posts, run without --dry-run")
        return
    
    # Confirm before proceeding (unless limit is small or force is set)
    if len(posts) > 20 and not limit and not force:
        print(f"⚠️  You're about to ingest {len(posts)} posts.")
        print("This will:")
        print("- Use Gemini API credits for vision/embeddings")
        print("- Store vectors in your Pinecone index")
        print("- Take approximately {} minutes".format(len(posts) * 2 / 60))
        
        response = input("\nContinue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Migration cancelled.")
            return
    
    # Initialize ingestion pipeline
    print("\nInitializing RAG ingestion pipeline...")
    try:
        pipeline = get_ingestion_pipeline()
        print("✓ Pipeline initialized\n")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {str(e)}")
        return
    
    # Process posts
    print("Starting ingestion...")
    print("=" * 60 + "\n")
    
    success_count = 0
    failed_count = 0
    failed_posts = []
    
    start_time = datetime.now()
    
    for i, post in enumerate(posts, 1):
        print(f"[{i}/{len(posts)}] Processing post {post.id}...", end=' ')
        
        try:
            success = pipeline.ingest_post(
                post_id=str(post.id),
                image_url=post.image_url,
                caption=post.caption or "",
                platform=post.platform,
                scheduled_time=post.scheduled_time
            )
            
            if success:
                # Mark as ingested in database
                post.rag_ingested = True
                db.session.commit()
                
                print("✓ SUCCESS")
                success_count += 1
            else:
                print("✗ FAILED (check logs)")
                failed_count += 1
                failed_posts.append(post.id)
        
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            logger.error(f"Failed to ingest post {post.id}: {str(e)}")
            failed_count += 1
            failed_posts.append(post.id)
        
        # Show progress every 10 posts
        if i % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            avg_time = elapsed / i
            remaining = (len(posts) - i) * avg_time
            print(f"\n  Progress: {i}/{len(posts)} ({i/len(posts)*100:.1f}%)")
            print(f"  Estimated time remaining: {remaining/60:.1f} minutes\n")
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)
    print(f"\n✓ Successfully ingested: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"⏱️  Total time: {duration/60:.1f} minutes")
    print(f"📊 Average time per post: {duration/len(posts):.1f} seconds")
    
    if failed_posts:
        print(f"\nFailed post IDs: {failed_posts}")
        print("You can try re-ingesting these manually or with --force")
    
    print("\n🎉 Your RAG system now has knowledge of {} posts!".format(success_count))
    print("\nNext steps:")
    print("1. Test the chat system: python quick_start_rag.py")
    print("2. Integrate auto-replies into your webhook handlers")
    print("3. Monitor token usage and adjust settings as needed")
    print()


def main():
    """Parse arguments and run migration."""
    parser = argparse.ArgumentParser(
        description='Migrate existing posts into RAG vector database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Only ingest first N posts (for testing)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-ingest posts even if already marked as ingested'
    )
    
    parser.add_argument(
        '--platform',
        type=str,
        choices=['instagram', 'linkedin'],
        default=None,
        help='Only ingest posts from specific platform'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be ingested without actually doing it'
    )
    
    args = parser.parse_args()
    
    # Run migration
    try:
        migrate_posts(
            limit=args.limit,
            force=args.force,
            platform=args.platform,
            dry_run=args.dry_run
        )
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user.")
        print("Progress has been saved. Run again to continue.")
    except Exception as e:
        logger.error(f"Migration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
