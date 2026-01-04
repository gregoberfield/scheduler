from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app import db, limiter
from app.models.availability import AvailabilitySlot, AggregateSlotCount
from app.models.user import User
from sqlalchemy import and_, or_
import json

bp = Blueprint('availability', __name__)

@bp.route('/my-availability')
@login_required
def my_availability():
    """Personal availability page"""
    return render_template('availability/my_availability.html')


@bp.route('/timeline')
@login_required
def timeline():
    """Guild timeline page"""
    return render_template('availability/timeline.html')


@bp.route('/heatmap')
@login_required
def heatmap():
    """Heatmap view page"""
    return render_template('availability/heatmap.html')


@bp.route('/api/availability', methods=['GET'])
@login_required
def get_availability():
    """Get availability data with filters"""
    start_slot = request.args.get('start_slot', type=int)
    end_slot = request.args.get('end_slot', type=int)
    user_id_param = request.args.get('user_id')
    wow_class = request.args.get('class')
    role = request.args.get('role')
    confidence = request.args.get('confidence', 'all')  # 'all', 'available', 'available_maybe'
    
    # Handle 'current' user_id
    if user_id_param == 'current':
        user_id = current_user.id
    else:
        user_id = int(user_id_param) if user_id_param else None
    
    # Build query
    query = AvailabilitySlot.query
    
    # Filter by slot range
    if start_slot is not None and end_slot is not None:
        query = query.filter(
            and_(
                AvailabilitySlot.slot_index >= start_slot,
                AvailabilitySlot.slot_index <= end_slot
            )
        )
    
    # Filter by user
    if user_id:
        query = query.filter(AvailabilitySlot.user_id == user_id)
    else:
        # Get users with filters
        user_query = User.query
        
        if wow_class:
            user_query = user_query.filter(User.wow_class == wow_class)
        
        if role:
            # Filter by role in JSON array
            user_query = user_query.filter(User.roles.like(f'%{role}%'))
        
        user_ids = [u.id for u in user_query.all()]
        if user_ids:
            query = query.filter(AvailabilitySlot.user_id.in_(user_ids))
    
    # Filter by confidence level
    if confidence == 'available':
        query = query.filter(AvailabilitySlot.state == 2)
    elif confidence == 'available_maybe':
        query = query.filter(AvailabilitySlot.state.in_([1, 2]))
    
    # Get slots
    slots = query.all()
    
    # Get users
    if user_id:
        users = [User.query.get(user_id)]
    else:
        user_ids = list(set(slot.user_id for slot in slots))
        users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    
    return jsonify({
        'slots': [slot.to_dict() for slot in slots],
        'users': [user.to_dict() for user in users]
    }), 200


@bp.route('/api/availability/bulk', methods=['POST'])
@login_required
@limiter.limit("100 per hour")
def bulk_update_availability():
    """Bulk update availability slots"""
    data = request.get_json()
    slots = data.get('slots', [])
    
    if not slots:
        return jsonify({'error': 'No slots provided'}), 400
    
    # Process each slot
    for slot_data in slots:
        slot_index = slot_data.get('slot_index')
        state = slot_data.get('state')
        
        if slot_index is None or state is None:
            continue
        
        # Validate state
        if state not in [0, 1, 2]:
            continue
        
        # Check if slot exists
        existing_slot = AvailabilitySlot.query.filter_by(
            user_id=current_user.id,
            slot_index=slot_index
        ).first()
        
        if existing_slot:
            # Update or delete
            if state == 0:
                # Remove unavailable slots to save space
                db.session.delete(existing_slot)
            else:
                existing_slot.state = state
        else:
            # Create new slot only if not unavailable
            if state != 0:
                new_slot = AvailabilitySlot(
                    user_id=current_user.id,
                    slot_index=slot_index,
                    state=state
                )
                db.session.add(new_slot)
    
    db.session.commit()
    
    return jsonify({'success': True}), 200


@bp.route('/api/availability/aggregate', methods=['GET'])
@login_required
def get_aggregate():
    """Get aggregate counts for heatmap"""
    start_slot = request.args.get('start_slot', type=int)
    end_slot = request.args.get('end_slot', type=int)
    
    query = AggregateSlotCount.query
    
    if start_slot is not None and end_slot is not None:
        query = query.filter(
            and_(
                AggregateSlotCount.slot_index >= start_slot,
                AggregateSlotCount.slot_index <= end_slot
            )
        )
    
    aggregates = query.all()
    
    return jsonify({
        'aggregates': [agg.to_dict() for agg in aggregates]
    }), 200
