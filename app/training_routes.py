"""
Training Data Management Routes
Manage events, community information, and other data used to train AI responses
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
import json
from . import db
from .models import TrainingData, User
from .auth import login_required, get_current_user

training_bp = Blueprint('training', __name__, url_prefix='/training')

@training_bp.route('/')
@login_required
def index():
    """View all training data"""
    category_filter = request.args.get('category', 'all')
    
    query = TrainingData.query
    
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    training_data = query.order_by(TrainingData.priority.desc(), TrainingData.created_at.desc()).all()
    
    # Get category counts
    categories = {
        'all': TrainingData.query.count(),
        'event': TrainingData.query.filter_by(category='event').count(),
        'community': TrainingData.query.filter_by(category='community').count(),
        'faq': TrainingData.query.filter_by(category='faq').count(),
        'product': TrainingData.query.filter_by(category='product').count(),
        'other': TrainingData.query.filter_by(category='other').count(),
    }
    
    return render_template('training/manage_data.html', 
                         training_data=training_data, 
                         category_filter=category_filter,
                         categories=categories)

@training_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_data():
    """Add new training data"""
    if request.method == 'POST':
        category = request.form.get('category', 'other')
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags_str = request.form.get('tags', '').strip()
        priority = int(request.form.get('priority', 5))
        is_active = request.form.get('is_active') == 'on'
        
        # Event-specific fields
        event_date_str = request.form.get('event_date', '').strip()
        location = request.form.get('location', '').strip()
        contact_info = request.form.get('contact_info', '').strip()
        
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('training.new_data'))
        
        # Parse tags
        tags = []
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        tags_json = json.dumps(tags) if tags else None
        
        # Parse event date
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.fromisoformat(event_date_str)
            except ValueError:
                flash('Invalid date format.', 'warning')
        
        # Create training data
        user = get_current_user()
        data = TrainingData(
            category=category,
            title=title,
            content=content,
            tags=tags_json,
            priority=priority,
            is_active=is_active,
            event_date=event_date,
            location=location if location else None,
            contact_info=contact_info if contact_info else None,
            created_by_id=user.id if user else None
        )
        
        db.session.add(data)
        db.session.commit()
        
        flash(f'Training data "{title}" added successfully!', 'success')
        return redirect(url_for('training.index'))
    
    return render_template('training/add_data.html')

@training_bp.route('/edit/<int:data_id>', methods=['GET', 'POST'])
@login_required
def edit_data(data_id):
    """Edit existing training data"""
    data = TrainingData.query.get_or_404(data_id)
    
    if request.method == 'POST':
        data.category = request.form.get('category', 'other')
        data.title = request.form.get('title', '').strip()
        data.content = request.form.get('content', '').strip()
        tags_str = request.form.get('tags', '').strip()
        data.priority = int(request.form.get('priority', 5))
        data.is_active = request.form.get('is_active') == 'on'
        
        # Event-specific fields
        event_date_str = request.form.get('event_date', '').strip()
        data.location = request.form.get('location', '').strip() or None
        data.contact_info = request.form.get('contact_info', '').strip() or None
        
        if not data.title or not data.content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('training.edit_data', data_id=data_id))
        
        # Parse tags
        tags = []
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        data.tags = json.dumps(tags) if tags else None
        
        # Parse event date
        if event_date_str:
            try:
                data.event_date = datetime.fromisoformat(event_date_str)
            except ValueError:
                data.event_date = None
        else:
            data.event_date = None
        
        db.session.commit()
        
        flash(f'Training data "{data.title}" updated successfully!', 'success')
        return redirect(url_for('training.index'))
    
    # Parse existing tags for display
    existing_tags = []
    if data.tags:
        try:
            existing_tags = json.loads(data.tags)
        except:
            pass
    
    return render_template('training/edit_data.html', data=data, existing_tags=existing_tags)

@training_bp.route('/delete/<int:data_id>', methods=['POST'])
@login_required
def delete_data(data_id):
    """Delete training data"""
    data = TrainingData.query.get_or_404(data_id)
    title = data.title
    
    db.session.delete(data)
    db.session.commit()
    
    flash(f'Training data "{title}" deleted successfully.', 'info')
    return redirect(url_for('training.index'))

@training_bp.route('/toggle/<int:data_id>', methods=['POST'])
@login_required
def toggle_active(data_id):
    """Toggle active status"""
    data = TrainingData.query.get_or_404(data_id)
    data.is_active = not data.is_active
    db.session.commit()
    
    status = 'activated' if data.is_active else 'deactivated'
    flash(f'Training data "{data.title}" {status}.', 'success')
    return redirect(url_for('training.index'))

@training_bp.route('/api/search', methods=['GET'])
@login_required
def search_api():
    """API endpoint to search training data"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    
    if not query:
        return jsonify([])
    
    search_query = TrainingData.query.filter(TrainingData.is_active == True)
    
    if category:
        search_query = search_query.filter(TrainingData.category == category)
    
    # Search in title, content, and tags
    search_pattern = f'%{query}%'
    search_query = search_query.filter(
        db.or_(
            TrainingData.title.like(search_pattern),
            TrainingData.content.like(search_pattern),
            TrainingData.tags.like(search_pattern)
        )
    )
    
    results = search_query.order_by(TrainingData.priority.desc()).limit(10).all()
    
    return jsonify([{
        'id': data.id,
        'category': data.category,
        'title': data.title,
        'content': data.content[:200] + '...' if len(data.content) > 200 else data.content,
        'priority': data.priority
    } for data in results])
