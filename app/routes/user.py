from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
import bleach

bp = Blueprint('user', __name__)

@bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """User profile edit page"""
    return render_template('user/profile.html')


@bp.route('/profile', methods=['POST'])
@login_required
def update_profile_form():
    """Update user profile from form submission"""
    wow_class = request.form.get('wow_class', '')
    roles = request.form.getlist('roles')
    password = request.form.get('password', '')
    
    # Validation
    if not wow_class:
        flash('Class is required.', 'danger')
        return redirect(url_for('user.profile'))
    
    # Update class
    current_user.wow_class = wow_class
    
    # Update roles
    current_user.set_roles(roles)
    
    # Update password if provided
    if password:
        current_user.set_password(password)
    
    db.session.commit()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('user.profile'))


@bp.route('/api/me', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    return jsonify(current_user.to_dict()), 200


@bp.route('/api/me', methods=['PUT'])
@login_required
def update_profile():
    """Update current user profile"""
    data = request.get_json()
    
    # Update allowed fields
    if 'roles' in data:
        current_user.set_roles(data['roles'])
    
    if 'timezone' in data:
        current_user.timezone = bleach.clean(data['timezone'])
    
    if 'wow_class' in data:
        current_user.wow_class = data['wow_class']
    
    # Update password if provided
    if 'password' in data and data['password']:
        current_user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200
