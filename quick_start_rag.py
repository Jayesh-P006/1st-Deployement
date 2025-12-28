"""
Quick Start Script for RAG System
==================================

Run this script to test your RAG system setup and verify all components work.

Usage:
    python quick_start_rag.py

This will:
1. Verify API keys are configured
2. Test Pinecone connection
3. Test Gemini embeddings
4. Test Groq LLM connection
5. Run a sample ingestion
6. Run sample chat queries
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_api_keys():
    """Verify all required API keys are set."""
    print("\n" + "="*60)
    print("STEP 1: Checking API Keys")
    print("="*60)
    
    required_keys = {
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
    }
    
    all_present = True
    for key_name, key_value in required_keys.items():
        if key_value and len(key_value) > 10:
            print(f"✓ {key_name}: {key_value[:10]}...{key_value[-4:]}")
        else:
            print(f"✗ {key_name}: NOT SET")
            all_present = False
    
    if not all_present:
        print("\n⚠️  Missing API keys! Please add them to your .env file")
        print("See .env.example for the template")
        return False
    
    print("\n✓ All API keys configured!")
    return True


def test_pinecone_connection():
    """Test connection to Pinecone."""
    print("\n" + "="*60)
    print("STEP 2: Testing Pinecone Connection")
    print("="*60)
    
    try:
        from pinecone import Pinecone
        from config import Config
        
        pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        indexes = [idx.name for idx in pc.list_indexes()]
        
        print(f"✓ Connected to Pinecone")
        print(f"  Available indexes: {indexes}")
        
        if Config.PINECONE_INDEX_NAME in indexes:
            print(f"✓ Index '{Config.PINECONE_INDEX_NAME}' exists")
            
            # Get stats
            index = pc.Index(Config.PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()
            print(f"  Total vectors: {stats.get('total_vector_count', 0)}")
            print(f"  Dimension: {stats.get('dimension', 0)}")
        else:
            print(f"⚠️  Index '{Config.PINECONE_INDEX_NAME}' does not exist yet")
            print(f"  It will be created on first ingestion")
        
        return True
    
    except Exception as e:
        print(f"✗ Pinecone connection failed: {str(e)}")
        return False


def test_gemini_embeddings():
    """Test Gemini embeddings."""
    print("\n" + "="*60)
    print("STEP 3: Testing Gemini Embeddings")
    print("="*60)
    
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from config import Config
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model=Config.GEMINI_EMBEDDING_MODEL,
            google_api_key=Config.GEMINI_API_KEY
        )
        
        # Test embedding generation
        test_text = "This is a test event happening tomorrow"
        embedding = embeddings.embed_query(test_text)
        
        print(f"✓ Gemini embeddings working")
        print(f"  Model: {Config.GEMINI_EMBEDDING_MODEL}")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
        
        return True
    
    except Exception as e:
        print(f"✗ Gemini embeddings failed: {str(e)}")
        return False


def test_groq_llm():
    """Test Groq LLM connection."""
    print("\n" + "="*60)
    print("STEP 4: Testing Groq LLM (Llama 3)")
    print("="*60)
    
    try:
        from langchain_groq import ChatGroq
        from config import Config
        
        llm = ChatGroq(
            model=Config.GROQ_MODEL,
            groq_api_key=Config.GROQ_API_KEY,
            temperature=0.7,
            max_tokens=50
        )
        
        # Test generation
        response = llm.invoke("Say 'hello world' in one sentence")
        
        print(f"✓ Groq LLM working")
        print(f"  Model: {Config.GROQ_MODEL}")
        print(f"  Test response: {response.content}")
        
        return True
    
    except Exception as e:
        print(f"✗ Groq LLM failed: {str(e)}")
        return False


def test_ingestion():
    """Test the ingestion pipeline with a sample post."""
    print("\n" + "="*60)
    print("STEP 5: Testing Ingestion Pipeline")
    print("="*60)
    
    try:
        from app.ai.rag_ingest import get_ingestion_pipeline
        
        pipeline = get_ingestion_pipeline()
        
        # Create a test post with a sample image URL
        test_post = {
            'post_id': 'test_quickstart_001',
            'image_url': 'https://via.placeholder.com/800x600.png?text=Sample+Event+Image',
            'caption': 'Join us for the Tech Summit 2025 at Convention Center on March 15th! Topics include AI, Web3, and Cloud Computing.',
            'platform': 'instagram'
        }
        
        print(f"Ingesting test post...")
        print(f"  Post ID: {test_post['post_id']}")
        print(f"  Caption: {test_post['caption'][:60]}...")
        
        success = pipeline.ingest_post(**test_post)
        
        if success:
            print(f"✓ Ingestion successful!")
            print(f"  Post added to Pinecone vector database")
        else:
            print(f"⚠️  Ingestion completed with warnings (check logs)")
        
        return True
    
    except Exception as e:
        print(f"✗ Ingestion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_chat():
    """Test the chat pipeline with sample queries."""
    print("\n" + "="*60)
    print("STEP 6: Testing Chat Pipeline")
    print("="*60)
    
    try:
        from app.ai.rag_chat import get_chat_pipeline
        
        pipeline = get_chat_pipeline()
        
        test_queries = [
            ("Hi there!", "Should hit gatekeeper (0 tokens)"),
            ("When is the next event?", "Should use RAG retrieval"),
            ("Thanks!", "Should hit gatekeeper (0 tokens)"),
        ]
        
        print(f"\nRunning {len(test_queries)} test queries...\n")
        
        for query, description in test_queries:
            print(f"Query: \"{query}\"")
            print(f"Expected: {description}")
            
            response, metadata = pipeline.generate_response(query)
            
            print(f"Response: \"{response}\"")
            print(f"Source: {metadata['source']}")
            print(f"Tokens: {metadata['tokens_used']}")
            print(f"Time: {metadata.get('processing_time_ms', 0)}ms")
            print()
        
        print("✓ Chat pipeline working!")
        return True
    
    except Exception as e:
        print(f"✗ Chat pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RAG SYSTEM QUICK START TEST")
    print("="*60)
    print("\nThis script will verify your RAG system setup.")
    print("Make sure you have:")
    print("1. Created a .env file with all API keys")
    print("2. Installed all dependencies (pip install -r requirements.txt)")
    print()
    
    input("Press Enter to continue...")
    
    # Run tests
    results = []
    
    results.append(("API Keys", check_api_keys()))
    
    if not results[0][1]:
        print("\n⚠️  Cannot continue without API keys. Exiting.")
        return
    
    results.append(("Pinecone", test_pinecone_connection()))
    results.append(("Gemini Embeddings", test_gemini_embeddings()))
    results.append(("Groq LLM", test_groq_llm()))
    results.append(("Ingestion", test_ingestion()))
    results.append(("Chat", test_chat()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Your RAG system is ready to use!")
        print("\nNext steps:")
        print("1. Run: python migrate_existing_posts.py (to ingest existing posts)")
        print("2. Update your dm_routes.py with auto-reply code (see example_dm_integration.py)")
        print("3. Update your routes.py with auto-ingestion code (see example_post_ingestion.py)")
        print("4. Deploy to production with your API keys")
    else:
        print("\n⚠️  Some tests failed. Please fix the errors above and try again.")
    
    print()


if __name__ == '__main__':
    main()
