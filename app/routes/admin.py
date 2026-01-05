from flask import Blueprint, render_template, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User
from app.models.availability import AvailabilitySlot, AggregateSlotCount
import csv
import io

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin or superuser access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if not (current_user.is_admin or current_user.is_superuser):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    users = User.query.order_by(User.created_at).all()
    return render_template('admin/index.html', users=users)


@bp.route('/api/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users"""
    users = User.query.order_by(User.created_at).all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200


@bp.route('/api/users/<int:user_id>/promote', methods=['POST'])
@login_required
@admin_required
def promote_user(user_id):
    """Promote user to admin"""
    if not current_user.is_superuser:
        return jsonify({'error': 'Only superusers can promote users'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200


@bp.route('/api/users/<int:user_id>/demote', methods=['POST'])
@login_required
@admin_required
def demote_user(user_id):
    """Demote user from admin"""
    if not current_user.is_superuser:
        return jsonify({'error': 'Only superusers can demote users'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Can't demote superuser
    if user.is_superuser:
        return jsonify({'error': 'Cannot demote superuser'}), 400
    
    user.is_admin = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200


@bp.route('/api/purge-schedule', methods=['POST'])
@login_required
@admin_required
def purge_schedule():
    """Purge all scheduling data (availability and aggregates) while preserving users"""
    if not current_user.is_superuser:
        return jsonify({'error': 'Only superusers can purge scheduling data'}), 403
    
    try:
        # Delete all availability slots
        availability_count = AvailabilitySlot.query.count()
        AvailabilitySlot.query.delete()
        
        # Delete all aggregate counts
        aggregate_count = AggregateSlotCount.query.count()
        AggregateSlotCount.query.delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Purged {availability_count} availability slots and {aggregate_count} aggregate counts',
            'availability_deleted': availability_count,
            'aggregates_deleted': aggregate_count
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to purge data: {str(e)}'}), 500


@bp.route('/api/export/roster', methods=['GET'])
@login_required
@admin_required
def export_roster():
    """Export roster as CSV"""
    users = User.query.order_by(User.character_name).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Character Name', 'Class', 'Roles', 'Timezone', 'Admin', 'Created At'])
    
    # Write data
    for user in users:
        roles = ', '.join(user.get_roles()) if user.get_roles() else ''
        writer.writerow([
            user.character_name,
            user.wow_class,
            roles,
            user.timezone or '',
            'Yes' if (user.is_admin or user.is_superuser) else 'No',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
        ])
    
    # Prepare response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='roster.csv'
    )
