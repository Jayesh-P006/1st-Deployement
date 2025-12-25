# 🚀 Social Media Post Scheduler

A collaborative social media management platform for teams to create, manage, and schedule posts across Instagram and LinkedIn with role-based permissions and AI-powered assistance.

## ✨ Features

### Core Features
- **Collaborative Draft System** - Team members work together on post drafts
- **Multi-Platform Support** - Schedule posts for Instagram and LinkedIn
- **Role-Based Access Control** - Lead, Co-Lead, and Member positions with different permissions
- **Vertical Organization** - Organize team by verticals (Content, Social Media, Design, Marketing, PR, etc.)
- **Draft Workflow** - Draft → Review → Approved → Scheduled → Published
- **Media Management** - Upload and manage images/videos for posts
- **Theme & Description** - Add context and categorization to drafts

### Advanced Features
- **AI Content Generation** - Gemini AI integration for content suggestions
- **Instagram DM Automation** - Automated responses and conversation management
- **Training Data Management** - Train AI with custom responses
- **Admin Dashboard** - User approval and management system
- **Real-time Progress Tracking** - Monitor draft completion status

## 📋 Prerequisites

- Python 3.8+
- MySQL Database
- Instagram Business Account (for Instagram features)
- LinkedIn Developer Account (for LinkedIn features)
- Google Gemini API Key (for AI features)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd "Auto-Post Posting system final"
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create `.env` file:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql://username:password@localhost/dbname
INSTAGRAM_ACCESS_TOKEN=your-instagram-token
INSTAGRAM_USER_ID=your-instagram-user-id
LINKEDIN_ACCESS_TOKEN=your-linkedin-token
LINKEDIN_USER_ID=your-linkedin-user-id
GEMINI_API_KEY=your-gemini-api-key
PUBLIC_URL=your-ngrok-url
WEBHOOK_VERIFY_TOKEN=your-webhook-token
```

### 5. Run Application
```bash
python run.py
```
Access at: `http://127.0.0.1:5000`

## 👥 User Roles & Permissions

| Role | Create Drafts | Edit Content | Edit Media | Edit Tags | Approve | Schedule |
|------|--------------|--------------|------------|-----------|---------|----------|
| **Lead** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Co-Lead** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Member** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

## 📁 Project Structure

```
app/
├── __init__.py              # Flask app initialization
├── models.py                # Database models (User, PostDraft, etc.)
├── auth.py                  # Authentication & user management
├── admin_routes.py          # Admin dashboard
├── collab_routes.py         # Collaborative drafts
├── routes.py                # Main routes
├── settings_routes.py       # Settings & DM management
├── training_routes.py       # AI training data
├── webhook_routes.py        # Instagram webhooks
├── utils.py                 # Utility functions
├── ai/
│   └── gemini_service.py    # AI integration
├── social/
│   ├── instagram.py         # Instagram API
│   ├── instagram_webhooks.py
│   └── linkedin.py          # LinkedIn API
├── static/css/
│   └── style.css            # Global styles
└── templates/
    ├── base.html            # Base template
    ├── auth/                # Login, register, profile
    ├── collab/              # Draft management
    ├── admin/               # Admin dashboard
    ├── settings/            # App settings
    └── training/            # AI training
```

## 🚀 Quick Start Guide

### First User Setup
1. Navigate to `/auth/register`
2. Fill registration form (first user becomes Admin)
3. Login with credentials

### Creating Your First Draft
1. Click **"+ New Draft"**
2. Enter title, select platform (Instagram/LinkedIn)
3. Add optional theme and description
4. Click **"Create Draft"**

### Working on Drafts
1. Click on draft from drafts list
2. Add **Content** (text for the post)
3. Upload **Media** (images/videos)
4. Add **Collaboration Tags** (PR & sponsorship tags)
5. Submit for review when complete

### Approving & Scheduling (Lead/Co-Lead Only)
1. Review completed draft
2. Click **"Approve Draft"**
3. Click **"Schedule Post"**
4. Select date, time, timezone
5. Confirm scheduling

## 🔧 Configuration

### Verticals Available
- Content and Innovation
- Social Media
- Design
- Marketing
- PR & Sponsorship
- Creatives
- Production
- Operations
- Technical

### Workflow Statuses
- **Draft** - Work in progress
- **Review** - Submitted for approval
- **Approved** - Approved by Lead/Co-Lead
- **Scheduled** - Scheduled for publishing
- **Published** - Successfully posted

## 🎨 For Frontend Developers

All templates are in `app/templates/` with inline styles for easy customization.

### Key Templates
- `base.html` - Navigation and layout
- `collab/drafts.html` - Drafts listing
- `collab/new_draft.html` - Create draft form
- `collab/edit_draft.html` - Edit draft (main workspace)
- `auth/register.html` - User registration
- `auth/login.html` - User login

### Styling
- Inline styles in templates for easy modification
- Global styles in `static/css/style.css`
- Color scheme: Blue (#667eea), Green (#28a745), Red (#dc3545)

## 🔌 API Integration

### Instagram Setup
1. Create Facebook Developer App
2. Get Instagram Business Account token
3. Configure webhook for DMs
4. Update `.env` with credentials

### LinkedIn Setup
1. Create LinkedIn Developer App
2. Get OAuth 2.0 token
3. Update `.env` with credentials

### AI Setup
1. Get Gemini API key from Google AI Studio
2. Add to `.env`
3. Train AI in Training section

## 🐛 Troubleshooting

**Database Connection Failed**
- Check MySQL is running
- Verify credentials in `.env`

**Instagram/LinkedIn Not Working**
- Verify tokens are valid and not expired
- Check API permissions

**File Upload Issues**
- Check `uploads/` directory exists and is writable
- Verify file size limits

## 🤝 Contributing

1. Frontend work: Modify templates in `app/templates/`
2. Backend work: Update routes in `app/*_routes.py`
3. Database changes: Update `app/models.py`
4. Follow existing code style and patterns

## 📝 Environment Variables

Required variables in `.env`:
```env
SECRET_KEY=                    # Flask secret key
DATABASE_URL=                  # MySQL connection string
INSTAGRAM_ACCESS_TOKEN=        # Instagram API token
INSTAGRAM_USER_ID=            # Instagram user ID
INSTAGRAM_BUSINESS_ACCOUNT_ID= # Instagram business account
WEBHOOK_VERIFY_TOKEN=         # Webhook verification
LINKEDIN_ACCESS_TOKEN=        # LinkedIn API token
LINKEDIN_USER_ID=             # LinkedIn user ID
GEMINI_API_KEY=               # Google Gemini AI key
PUBLIC_URL=                   # Public URL for webhooks (ngrok)
```

## 📄 License

Educational/Internal Use

## 👨‍💻 Support

For issues or questions, contact your development team.

---

**Note**: Keep `.env` file secure and never commit to version control!
