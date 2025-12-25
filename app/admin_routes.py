from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from .models import User
from . import db
from .auth import login_required, role_required
import requests

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/manage_requests', methods=['GET'])
@login_required
@role_required('admin')
def manage_requests():
    pending_users = User.query.filter_by(is_active=False).all()
    return render_template('admin/manage_requests.html', pending_users=pending_users)

@admin_bp.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get vertical and position from form
    new_vertical = request.form.get('vertical')
    new_position = request.form.get('position')
    
    # Update user fields
    if new_vertical:
        user.vertical = new_vertical
    if new_position:
        user.position = new_position
        # Set role based on position for backward compatibility
        if new_position in ['Lead', 'Co-Lead']:
            user.role = 'approver'
        else:
            user.role = 'creative'
    
    user.is_active = True
    db.session.commit()
    flash(f"User '{user.username}' approved and activated.", 'success')
    return redirect(url_for('admin.manage_requests'))

@admin_bp.route('/deny_user/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def deny_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' denied and removed.", 'info')
    return redirect(url_for('admin.manage_requests'))

# ============= WEBHOOK MANAGEMENT =============

@admin_bp.route('/webhooks')
@login_required
@role_required('admin')
def webhooks():
    """Webhook management dashboard"""
    # Get current webhook URL
    public_url = current_app.config.get('PUBLIC_URL', 'http://127.0.0.1:5000')
    webhook_url = f"{public_url}/webhook/instagram"
    verify_token = current_app.config.get('WEBHOOK_VERIFY_TOKEN', '')
    
    # Check webhook status with Instagram
    webhook_status = check_instagram_webhook_status()
    
    return render_template('admin/webhooks.html',
                         webhook_url=webhook_url,
                         verify_token=verify_token,
                         webhook_status=webhook_status)

@admin_bp.route('/webhooks/subscribe', methods=['POST'])
@login_required
@role_required('admin')
def subscribe_webhook():
    """Subscribe to Instagram webhook"""
    access_token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
    business_id = current_app.config.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    public_url = current_app.config.get('PUBLIC_URL', 'http://127.0.0.1:5000')
    verify_token = current_app.config.get('WEBHOOK_VERIFY_TOKEN', '')
    
    if not access_token or not business_id:
        flash('Instagram credentials not configured.', 'error')
        return redirect(url_for('admin.webhooks'))
    
    if not verify_token:
        flash('WEBHOOK_VERIFY_TOKEN not configured.', 'error')
        return redirect(url_for('admin.webhooks'))
    
    # Construct webhook URL
    callback_url = f"{public_url}/webhook/instagram"
    
    # Subscribe to Instagram webhooks via Graph API
    # This typically requires app-level configuration, not page-level
    # Endpoint: POST /{app-id}/subscriptions
    # For now, we'll provide instructions
    
    flash('Please configure webhooks in your Facebook App Dashboard. See instructions below.', 'info')
    return redirect(url_for('admin.webhooks'))

@admin_bp.route('/webhooks/status')
@login_required
@role_required('admin')
def webhook_status_api():
    """API endpoint to check webhook status"""
    status = check_instagram_webhook_status()
    return jsonify(status)

def check_instagram_webhook_status():
    """Check if Instagram webhook is properly configured"""
    access_token = current_app.config.get('INSTAGRAM_ACCESS_TOKEN')
    business_id = current_app.config.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    app_secret = current_app.config.get('INSTAGRAM_APP_SECRET')
    
    status = {
        'configured': False,
        'access_token': bool(access_token),
        'business_id': bool(business_id),
        'app_secret': bool(app_secret),
        'public_url': current_app.config.get('PUBLIC_URL', 'http://127.0.0.1:5000'),
        'verify_token': bool(current_app.config.get('WEBHOOK_VERIFY_TOKEN')),
        'webhook_url': f"{current_app.config.get('PUBLIC_URL', 'http://127.0.0.1:5000')}/webhook/instagram"
    }
    
    status['configured'] = all([
        status['access_token'],
        status['business_id'],
        status['verify_token']
    ])
    
    return status
