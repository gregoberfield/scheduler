from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
import bleach

bp = Blueprint('user', __name__, url_prefix='/api')

@bp.route('/me', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    return jsonify(current_user.to_dict()), 200


@bp.route('/me', methods=['PUT'])
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
