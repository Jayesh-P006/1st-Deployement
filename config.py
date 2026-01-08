import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

def get_database_url():
    """Build database URL from Railway environment variables or fallback to default."""
    # Check for Railway MySQL environment variables
    mysql_host = os.getenv('MYSQLHOST')
    mysql_port = os.getenv('MYSQLPORT', '3306')
    mysql_user = os.getenv('MYSQLUSER')
    mysql_password = os.getenv('MYSQLPASSWORD', '')
    mysql_database = os.getenv('MYSQLDATABASE')
    
    # If Railway MySQL variables are set, build the URL
    if mysql_host and mysql_user and mysql_database:
        return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    
    # Check for MYSQL_URL (Railway also provides this)
    mysql_url = os.getenv('MYSQL_URL')
    if mysql_url:
        # Railway MYSQL_URL format: mysql://user:pass@host:port/db
        # SQLAlchemy needs: mysql+pymysql://user:pass@host:port/db
        if mysql_url.startswith('mysql://'):
            return mysql_url.replace('mysql://', 'mysql+pymysql://', 1)
        return mysql_url
    
    # Check for generic DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Handle postgres:// -> postgresql:// conversion
        if database_url.startswith('postgres://'):
            return database_url.replace('postgres://', 'postgresql://', 1)
        # Handle mysql:// -> mysql+pymysql:// conversion
        if database_url.startswith('mysql://'):
            return database_url.replace('mysql://', 'mysql+pymysql://', 1)
        return database_url
    
    # Default for local development
    return 'mysql+pymysql://root:@localhost:3306/social_post_scheduler'

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database Configuration - auto-detects Railway MySQL or PostgreSQL
    SQLALCHEMY_DATABASE_URI = get_database_url()
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLAlchemy engine options for Railway MySQL SSL connections
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    SCHEDULER_API_ENABLED = True
    
    # Public URL for serving uploaded files (required for Instagram API)
    # Set RAILWAY_PUBLIC_DOMAIN or PUBLIC_URL in Railway environment variables
    # Railway automatically provides RAILWAY_PUBLIC_DOMAIN or RAILWAY_STATIC_URL
    RAILWAY_DOMAIN = os.getenv('RAILWAY_PUBLIC_DOMAIN', '') or os.getenv('RAILWAY_STATIC_URL', '')
    # Remove protocol from RAILWAY_STATIC_URL if present
    if RAILWAY_DOMAIN.startswith(('http://', 'https://')):
        RAILWAY_DOMAIN = RAILWAY_DOMAIN.split('://', 1)[1]
    PUBLIC_URL = os.getenv('PUBLIC_URL', f'https://{RAILWAY_DOMAIN}' if RAILWAY_DOMAIN else 'http://127.0.0.1:5000')
    
    # Instagram Configuration
    # Set these as environment variables in Railway
    INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # Timezone Configuration (for converting user input to UTC)
    # Set to your local timezone, e.g., 'Asia/Kolkata' for IST
    APP_TIMEZONE = os.getenv('APP_TIMEZONE', 'Asia/Kolkata')
    
    # Instagram Webhook Configuration
    WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN', 'your-secure-verify-token-123')
    INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET', '')  # For signature verification
