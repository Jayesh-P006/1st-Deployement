import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database Configuration
    # Supports both MySQL and PostgreSQL (Railway provides PostgreSQL)
    # Format MySQL: mysql+pymysql://username:password@localhost:3306/database_name
    # Format PostgreSQL: postgresql://username:password@host:port/database_name
    DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost:3306/social_post_scheduler')
    
    # Railway uses postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    SCHEDULER_API_ENABLED = True
    
    # Public URL for serving uploaded files (required for Instagram API)
    # Set RAILWAY_PUBLIC_DOMAIN or PUBLIC_URL in Railway environment variables
    RAILWAY_DOMAIN = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
    PUBLIC_URL = os.getenv('PUBLIC_URL', f'https://{RAILWAY_DOMAIN}' if RAILWAY_DOMAIN else 'http://127.0.0.1:5000')
    
    # Instagram Configuration
    # Set these as environment variables in Railway
    INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')
    
    # LinkedIn Configuration
    LINKEDIN_ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    LINKEDIN_ORGANIZATION_ID = os.getenv('LINKEDIN_ORGANIZATION_ID', '')
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')
    
    # Instagram Webhook Configuration
    WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN', 'your-secure-verify-token-123')
    INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET', '')  # For signature verification
