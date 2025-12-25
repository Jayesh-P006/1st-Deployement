from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(32), nullable=False)  # admin|creative|production|pr_sponsorship|approver (kept for backward compatibility)
    vertical = db.Column(db.String(64), nullable=True)  # Content and Innovation|Social Media|Design|Marketing|PR & Sponsorship|Creatives|Production|Operations|Technical
    position = db.Column(db.String(32), nullable=True)  # Lead|Co-Lead|Member
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    created_drafts = db.relationship('PostDraft', foreign_keys='PostDraft.created_by_id', backref='creator', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    activities = db.relationship('Activity', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_role_display(self):
        if self.vertical and self.position:
            return f"{self.vertical} - {self.position}"
        # Fallback for old role system
        role_names = {
            'admin': 'Administrator',
            'creative': 'Creative Team',
            'production': 'Production Team',
            'pr_sponsorship': 'PR & Sponsorship',
            'approver': 'Content Approver'
        }
        return role_names.get(self.role, self.role)
    
    def can_edit_content(self):
        # Lead and Co-Lead have all permissions, Members can write content
        if self.position in ['Lead', 'Co-Lead']:
            return True
        if self.position == 'Member':
            return True
        # Fallback for old role system
        return self.role in ['admin', 'creative', 'approver']
    
    def can_edit_media(self):
        # Lead and Co-Lead have all permissions, Members can add media
        if self.position in ['Lead', 'Co-Lead']:
            return True
        if self.position == 'Member':
            return True
        # Fallback for old role system
        return self.role in ['admin', 'production', 'approver']
    
    def can_edit_tags(self):
        # Lead and Co-Lead have all permissions, Members can add PR sponsorship tags
        if self.position in ['Lead', 'Co-Lead']:
            return True
        if self.position == 'Member':
            return True
        # Fallback for old role system
        return self.role in ['admin', 'pr_sponsorship', 'approver']
    
    def can_approve(self):
        # Only Lead and Co-Lead can approve
        if self.position in ['Lead', 'Co-Lead']:
            return True
        # Fallback for old role system
        return self.role in ['admin', 'approver']
    
    def can_schedule(self):
        # Only Lead and Co-Lead can schedule
        if self.position in ['Lead', 'Co-Lead']:
            return True
        # Fallback for old role system
        return self.role in ['admin', 'approver']
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class PostDraft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(32), nullable=False)
    theme = db.Column(db.String(200))  # Optional theme/category
    description = db.Column(db.Text)  # Optional description/brief
    content = db.Column(db.Text)
    image_path = db.Column(db.Text)  # JSON array
    collaboration_tags = db.Column(db.Text)  # JSON array of tags/mentions
    
    # Workflow status
    workflow_status = db.Column(db.String(32), default='draft')  # draft|review|approved|scheduled|published
    
    # Team completion tracking
    content_status = db.Column(db.String(32), default='pending')  # pending|completed|approved
    media_status = db.Column(db.String(32), default='pending')
    tags_status = db.Column(db.String(32), default='pending')
    
    # Assignment
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_creative = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_production = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_pr = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Scheduled post reference
    scheduled_post_id = db.Column(db.Integer, db.ForeignKey('scheduled_post.id'))
    scheduled_time = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    content_completed_at = db.Column(db.DateTime)
    media_completed_at = db.Column(db.DateTime)
    tags_completed_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    comments = db.relationship('Comment', backref='draft', lazy='dynamic', cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='draft', lazy='dynamic', cascade='all, delete-orphan')
    scheduled_post = db.relationship('ScheduledPost', backref='draft', uselist=False)
    
    # Team member relationships
    assigned_creative_user = db.relationship('User', foreign_keys=[assigned_creative], lazy='joined')
    assigned_production_user = db.relationship('User', foreign_keys=[assigned_production], lazy='joined')
    assigned_pr_user = db.relationship('User', foreign_keys=[assigned_pr], lazy='joined')
    approver = db.relationship('User', foreign_keys=[approved_by_id], lazy='joined')
    
    def get_completion_percentage(self):
        completed = 0
        total = 3
        if self.content_status == 'completed':
            completed += 1
        if self.media_status == 'completed':
            completed += 1
        if self.tags_status == 'completed':
            completed += 1
        return int((completed / total) * 100)
    
    def is_ready_for_review(self):
        return (self.content_status == 'completed' and 
                self.media_status == 'completed' and 
                self.tags_status == 'completed')
    
    def __repr__(self):
        return f'<PostDraft {self.id} {self.title} ({self.workflow_status})>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('post_draft.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(32), default='general')  # general|feedback|approval|revision
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment {self.id} by User {self.user_id}>'

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('post_draft.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'created_draft', 'updated_content', 'uploaded_media', etc.
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Activity {self.id} {self.action}>'

class ScheduledPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), nullable=False)  # 'instagram' or 'linkedin'
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.Text)  # JSON array of image paths for multiple images
    collaboration_tags = db.Column(db.Text)  # JSON array of tags/mentions
    scheduled_time = db.Column(db.DateTime, nullable=False)  # stored UTC
    status = db.Column(db.String(32), default='scheduled')  # scheduled|posted|failed|missed
    error_message = db.Column(db.String(512))
    token_used = db.Column(db.Integer, default=0)  # API tokens consumed for this post
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScheduledPost {self.id} {self.platform} {self.status}>'

class TokenUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), nullable=False, unique=True)  # 'instagram' or 'linkedin'
    total_limit = db.Column(db.Integer, default=0)  # Daily/hourly limit
    used_today = db.Column(db.Integer, default=0)
    last_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    def remaining(self):
        return max(0, self.total_limit - self.used_today)
    
    def __repr__(self):
        return f'<TokenUsage {self.platform} {self.used_today}/{self.total_limit}>'

# ============= NEW MODELS FOR DM AUTOMATION =============

class ChatSettings(db.Model):
    """Global settings for chat automation features"""
    id = db.Column(db.Integer, primary_key=True)
    auto_reply_enabled = db.Column(db.Boolean, default=False)
    auto_comment_enabled = db.Column(db.Boolean, default=False)
    reply_rate_limit = db.Column(db.Integer, default=10)  # Max replies per hour
    comment_rate_limit = db.Column(db.Integer, default=20)  # Max comments per hour
    blacklist_keywords = db.Column(db.Text)  # JSON array of keywords to ignore
    whitelist_users = db.Column(db.Text)  # JSON array of prioritized users
    default_greeting = db.Column(db.Text, default="Hello! Thanks for reaching out. How can I help you today?")
    fallback_message = db.Column(db.Text, default="I'm sorry, I didn't quite understand that. Could you please rephrase?")
    business_hours_only = db.Column(db.Boolean, default=False)
    business_hours_start = db.Column(db.String(5), default="09:00")  # HH:MM format
    business_hours_end = db.Column(db.String(5), default="18:00")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatSettings auto_reply={self.auto_reply_enabled} auto_comment={self.auto_comment_enabled}>'

class TrainingData(db.Model):
    """Store information for training AI responses (events, community info, FAQs)"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # 'event', 'community', 'faq', 'product', 'other'
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text)  # JSON array of searchable tags
    priority = db.Column(db.Integer, default=5)  # 1-10, higher = more important
    is_active = db.Column(db.Boolean, default=True)
    event_date = db.Column(db.DateTime)  # For events
    location = db.Column(db.String(200))  # For events
    contact_info = db.Column(db.Text)  # Additional contact details
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref='training_data', lazy='joined')
    
    def __repr__(self):
        return f'<TrainingData {self.category}: {self.title}>'

class DMConversation(db.Model):
    """Track DM conversations with users"""
    id = db.Column(db.Integer, primary_key=True)
    instagram_user_id = db.Column(db.String(100), nullable=False)  # Instagram PSID
    instagram_username = db.Column(db.String(100))
    platform = db.Column(db.String(32), default='instagram')
    conversation_status = db.Column(db.String(32), default='active')  # active|resolved|archived
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    message_count = db.Column(db.Integer, default=0)
    auto_reply_count = db.Column(db.Integer, default=0)
    sentiment = db.Column(db.String(32))  # positive|neutral|negative
    tags = db.Column(db.Text)  # JSON array
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('DMMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan', order_by='DMMessage.created_at')
    
    def __repr__(self):
        return f'<DMConversation {self.instagram_username} ({self.message_count} msgs)>'

class DMMessage(db.Model):
    """Individual messages in a DM conversation"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('dm_conversation.id'), nullable=False)
    instagram_message_id = db.Column(db.String(100), unique=True)  # Instagram's message ID
    sender_type = db.Column(db.String(32), nullable=False)  # 'user' or 'bot'
    message_text = db.Column(db.Text, nullable=False)
    is_auto_reply = db.Column(db.Boolean, default=False)
    gemini_prompt_used = db.Column(db.Text)  # Store the prompt for debugging
    gemini_response_time = db.Column(db.Float)  # Response time in seconds
    sent_successfully = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DMMessage {self.sender_type} at {self.created_at}>'
