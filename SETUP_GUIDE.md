# 🚀 Setup Guide - Social Media Post Scheduler

This guide will help you set up the application from scratch for development or testing.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Recommended: Python 3.10 or later)
- **MySQL 5.7+** or **MariaDB 10.3+**
- **Git** (for cloning the repository)
- **pip** (Python package manager)

---

## 🗄️ Database Setup

### Step 1: Create MySQL Database

Open MySQL command line or your preferred MySQL client (phpMyAdmin, MySQL Workbench, etc.) and run:

```sql
CREATE DATABASE social_post_scheduler CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2: Create Tables and Insert Admin User

Run the following SQL script to create all required tables and insert a default admin account:

```sql
USE social_post_scheduler;

-- Users Table
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(120),
    role VARCHAR(32) NOT NULL DEFAULT 'admin',
    vertical VARCHAR(64),
    position VARCHAR(32),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Post Draft Table
CREATE TABLE post_draft (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    platform VARCHAR(32) NOT NULL,
    theme VARCHAR(200),
    description TEXT,
    content TEXT,
    image_path TEXT,
    collaboration_tags TEXT,
    workflow_status VARCHAR(32) DEFAULT 'draft',
    content_status VARCHAR(32) DEFAULT 'pending',
    media_status VARCHAR(32) DEFAULT 'pending',
    tags_status VARCHAR(32) DEFAULT 'pending',
    created_by_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    submitted_at DATETIME,
    approved_at DATETIME,
    approved_by_id INT,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_workflow_status (workflow_status),
    INDEX idx_created_by (created_by_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Social Post Table
CREATE TABLE social_post (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    image_path TEXT,
    scheduled_time DATETIME NOT NULL,
    status VARCHAR(32) DEFAULT 'scheduled',
    error_message TEXT,
    posted_at DATETIME,
    token_used INT DEFAULT 0,
    post_url VARCHAR(512),
    draft_id INT,
    FOREIGN KEY (draft_id) REFERENCES post_draft(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_scheduled_time (scheduled_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- API Usage Table
CREATE TABLE api_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(32) NOT NULL,
    used_today INT DEFAULT 0,
    total_limit INT DEFAULT 200,
    last_reset DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Comment Table
CREATE TABLE comment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    draft_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (draft_id) REFERENCES post_draft(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_draft_id (draft_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activity Log Table
CREATE TABLE activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    draft_id INT,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (draft_id) REFERENCES post_draft(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_draft_id (draft_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Training Data Table
CREATE TABLE training_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instagram Conversation Table
CREATE TABLE instagram_conversation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id VARCHAR(255) UNIQUE NOT NULL,
    sender_id VARCHAR(255) NOT NULL,
    sender_username VARCHAR(255),
    sender_name VARCHAR(255),
    last_message TEXT,
    last_message_time DATETIME,
    unread_count INT DEFAULT 0,
    status VARCHAR(32) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sender_id (sender_id),
    INDEX idx_status (status),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instagram Message Table
CREATE TABLE instagram_message (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    sender_id VARCHAR(255) NOT NULL,
    recipient_id VARCHAR(255),
    message_text TEXT,
    message_type VARCHAR(32) DEFAULT 'text',
    media_url TEXT,
    timestamp DATETIME NOT NULL,
    is_from_business BOOLEAN DEFAULT FALSE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES instagram_conversation(id) ON DELETE CASCADE,
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert Default Admin User
-- Password: admin123 (hashed using werkzeug.security)
INSERT INTO user (username, email, password_hash, full_name, role, vertical, position, is_active, created_at)
VALUES (
    'Admin',
    'trialadmin@gmail.com',
    'scrypt:32768:8:1$YgxYJM8sPRt16yCH$08b4003fec42b33ef9cb1835bbc9ee24937b9cae0eb71fe5a33a4247a215cbd8ac48d968c407e10315ebf46f20a1ddddf3e84960585367169ce2d3b0bbcafe3d',
    'ADMIN',
    'admin',
    'Operations',
    'Lead',
    TRUE,
    NOW()
);

-- Initialize API Usage for Instagram only
INSERT INTO api_usage (platform, used_today, total_limit, last_reset)
VALUES 
    ('instagram', 0, 200, NOW());
```

---

## 🔧 Application Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Jayesh-P006/SIH-2025.git
cd SIH-2025
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development

# Database Configuration
# Format: mysql+pymysql://username:password@host:port/database_name
DATABASE_URL=mysql+pymysql://root:@localhost:3306/social_post_scheduler

# Public URL (for Instagram API - use ngrok for development)
PUBLIC_URL=http://127.0.0.1:5000

# Instagram Configuration (Optional - for posting features)
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_business_account_id

# Gemini AI Configuration (Optional - for AI features)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro

# Instagram Webhook Configuration (Optional - for DM features)
WEBHOOK_VERIFY_TOKEN=your-secure-verify-token-123
INSTAGRAM_APP_SECRET=your_instagram_app_secret
```

**Note:** Replace the placeholders with your actual credentials. The application will work without social media API keys, but posting features will be disabled.

### Step 5: Create Required Directories

```bash
mkdir uploads
```

### Step 6: Run the Application

```bash
python run.py
```

The application will be available at: **http://127.0.0.1:5000**

---

## 🔐 Default Admin Credentials

Use these credentials to login for the first time:

- **Username:** `Admin`
- **Password:** `admin123`
- **Email:** `trialadmin@gmail.com`

**⚠️ IMPORTANT:** Change the admin password immediately after first login in production!

---

## 📝 Post-Setup Configuration

### 1. Change Admin Password
- Login with default credentials
- Go to Profile → Change password

### 2. Configure Social Media APIs (Optional)
- **Instagram:** Get access token from Meta Developer Console
- **Gemini AI:** Get API key from Google AI Studio

### 3. Create Additional Users
- Login as admin
- Navigate to Admin panel
- Approve user registration requests

---

## 🔄 Database Migrations

If you need to add new columns or modify the database schema in the future:

1. **Backup your database first**
2. Run manual ALTER TABLE commands, or
3. Use the migration scripts provided in the root directory

Example:
```bash
python migrate_user_fields.py
python migrate_draft_fields.py
```

---

## 🐛 Troubleshooting

### Database Connection Error
- Verify MySQL is running: `mysql -u root -p`
- Check DATABASE_URL in `.env` file
- Ensure database `social_post_scheduler` exists

### Import Errors
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### Port Already in Use
- Change port in `run.py`: `app.run(port=5001)`

### Uploads Not Working
- Ensure `uploads/` directory exists
- Check folder permissions

---

## 📚 Additional Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Instagram Graph API:** https://developers.facebook.com/docs/instagram-api/

---

## 👥 Team Collaboration

For team members working on the frontend:
- See `FRONTEND_GUIDE.md` for frontend-specific setup
- All templates are in `app/templates/`
- CSS is organized as internal CSS in each template + shared styles in `app/static/css/style.css`

---

## 🆘 Need Help?

If you encounter any issues during setup:
1. Check the error message carefully
2. Verify all prerequisites are installed
3. Ensure database credentials are correct
4. Check Python and MySQL versions

---

**Setup completed! 🎉** You're ready to start developing or testing the application.
