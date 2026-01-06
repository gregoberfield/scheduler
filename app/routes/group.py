"""
Group routes for WoW TBC party system.
Handles group creation, invitations, membership management, and visualization.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db, limiter
from app.models.group import Group, GroupMembership, GroupInvite
from app.models.user import User
from app.models.availability import AvailabilitySlot, AggregateSlotCount
from app.utils.group_names import generate_unique_group_name
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('group', __name__)


def expire_old_invites():
    """Mark invites older than 7 days as expired"""
    cutoff = datetime.utcnow() - timedelta(days=7)
    old_invites = GroupInvite.query.filter(
        GroupInvite.status == 'pending',
        GroupInvite.created_at < cutoff
    ).all()
    
    for invite in old_invites:
        invite.status = 'expired'
        invite.responded_at = datetime.utcnow()
    
    if old_invites:
        db.session.commit()
    
    return len(old_invites)


# ============= WEB PAGES =============

@bp.route('/groups')
@login_required
def index():
    """List all groups the user is a member of or leads"""
    # Get groups where user is a member
    memberships = GroupMembership.query.filter_by(user_id=current_user.id).all()
    member_group_ids = [m.group_id for m in memberships]
    
    my_groups = Group.query.filter(Group.id.in_(member_group_ids)).all() if member_group_ids else []
    
    return render_template('groups/index.html', groups=my_groups)


@bp.route('/groups/create', methods=['GET'])
@login_required
def create_page():
    """Show group creation confirmation page"""
    return render_template('groups/create.html')


@bp.route('/groups/<int:group_id>')
@login_required
def detail(group_id):
    """Show group details, members, and invite interface"""
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member
    if not group.is_member(current_user.id):
        flash('You are not a member of this group.', 'danger')
        return redirect(url_for('group.index'))
    
    # Get all users for invite dropdown
    all_users = User.query.order_by(User.character_name).all()
    
    # Filter out current members and users with pending invites
    member_ids = [m.user_id for m in group.memberships.all()]
    pending_invite_ids = [i.invitee_id for i in group.invites.filter_by(status='pending').all()]
    excluded_ids = set(member_ids + pending_invite_ids)
    
    available_users = [u for u in all_users if u.id not in excluded_ids]
    
    return render_template('groups/detail.html', 
                          group=group, 
                          available_users=available_users)


@bp.route('/groups/<int:group_id>/schedule')
@login_required
def schedule(group_id):
    """Show group availability heatmap"""
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member
    if not group.is_member(current_user.id):
        flash('You are not a member of this group.', 'danger')
        return redirect(url_for('group.index'))
    
    members = group.get_members()
    # Convert User objects to dictionaries for JSON serialization
    members_data = [m.to_dict() for m in members]
    
    return render_template('groups/schedule.html', group=group, members=members, members_data=members_data)


@bp.route('/invitations')
@login_required
def invitations():
    """Show pending invitations for current user"""
    # Expire old invites first
    expire_old_invites()
    
    # Get pending invites created within last 3 days
    cutoff = datetime.utcnow() - timedelta(days=3)
    pending_invites = GroupInvite.query.filter(
        GroupInvite.invitee_id == current_user.id,
        GroupInvite.status == 'pending',
        GroupInvite.created_at >= cutoff
    ).order_by(GroupInvite.created_at.desc()).all()
    
    return render_template('invitations/index.html', invites=pending_invites)


# ============= API ENDPOINTS =============

@bp.route('/api/groups', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def create_group():
    """Create a new group with auto-generated name"""
    try:
        # Generate unique name
        name = generate_unique_group_name()
        
        # Create group
        group = Group(
            name=name,
            leader_id=current_user.id
        )
        db.session.add(group)
        db.session.flush()  # Get group ID
        
        # Add creator as first member
        membership = GroupMembership(
            group_id=group.id,
            user_id=current_user.id
        )
        db.session.add(membership)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'group': group.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create group: {str(e)}'}), 500


@bp.route('/api/groups/<int:group_id>/invite', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def invite_user(group_id):
    """Invite a user to join the group"""
    group = Group.query.get_or_404(group_id)
    
    # Check if current user is the leader
    if not group.is_leader(current_user.id):
        return jsonify({'error': 'Only the group leader can send invites'}), 403
    
    # Check if group is full
    if group.is_full():
        return jsonify({'error': 'Group is full (5/5 members)'}), 400
    
    data = request.get_json()
    invitee_id = data.get('user_id')
    
    if not invitee_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # Check if user exists
    invitee = User.query.get(invitee_id)
    if not invitee:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is already a member
    if group.is_member(invitee_id):
        return jsonify({'error': 'User is already a member of this group'}), 400
    
    # Check if invite already exists
    existing_invite = GroupInvite.query.filter_by(
        group_id=group_id,
        invitee_id=invitee_id
    ).first()
    
    if existing_invite and existing_invite.status == 'pending':
        return jsonify({'error': 'Invite already pending for this user'}), 400
    
    # Create invite
    invite = GroupInvite(
        group_id=group_id,
        inviter_id=current_user.id,
        invitee_id=invitee_id,
        status='pending'
    )
    db.session.add(invite)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'invite': invite.to_dict()
    }), 201


@bp.route('/api/groups/<int:group_id>/invites/<int:invite_id>/accept', methods=['POST'])
@login_required
def accept_invite(group_id, invite_id):
    """Accept a group invitation"""
    invite = GroupInvite.query.get_or_404(invite_id)
    
    # Verify invite belongs to current user and this group
    if invite.invitee_id != current_user.id:
        return jsonify({'error': 'This invite is not for you'}), 403
    
    if invite.group_id != group_id:
        return jsonify({'error': 'Invite does not match group'}), 400
    
    if invite.status != 'pending':
        return jsonify({'error': f'Invite is {invite.status}'}), 400
    
    group = Group.query.get_or_404(group_id)
    
    # Check if group is full
    if group.is_full():
        return jsonify({'error': 'Group is now full'}), 400
    
    # Accept invite
    invite.status = 'accepted'
    invite.responded_at = datetime.utcnow()
    
    # Add user to group
    membership = GroupMembership(
        group_id=group_id,
        user_id=current_user.id
    )
    db.session.add(membership)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'You joined {group.name}!',
        'group': group.to_dict()
    }), 200


@bp.route('/api/groups/<int:group_id>/invites/<int:invite_id>/decline', methods=['POST'])
@login_required
def decline_invite(group_id, invite_id):
    """Decline a group invitation"""
    invite = GroupInvite.query.get_or_404(invite_id)
    
    # Verify invite belongs to current user
    if invite.invitee_id != current_user.id:
        return jsonify({'error': 'This invite is not for you'}), 403
    
    if invite.status != 'pending':
        return jsonify({'error': f'Invite is already {invite.status}'}), 400
    
    # Decline invite
    invite.status = 'declined'
    invite.responded_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Invite declined'
    }), 200


@bp.route('/api/groups/<int:group_id>/leave', methods=['DELETE'])
@login_required
def leave_group(group_id):
    """Leave a group (with leader auto-promotion)"""
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member
    membership = GroupMembership.query.filter_by(
        group_id=group_id,
        user_id=current_user.id
    ).first()
    
    if not membership:
        return jsonify({'error': 'You are not a member of this group'}), 400
    
    # If user is leader and there are other members, promote the next member
    is_leader = group.is_leader(current_user.id)
    remaining_members = group.memberships.filter(GroupMembership.user_id != current_user.id).all()
    
    if is_leader and remaining_members:
        # Promote member with earliest join date
        next_leader = min(remaining_members, key=lambda m: m.joined_at)
        group.leader_id = next_leader.user_id
    
    # Remove membership
    db.session.delete(membership)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'You left {group.name}'
    }), 200


@bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
@login_required
def disband_group(group_id):
    """Disband a group (leader only)"""
    group = Group.query.get_or_404(group_id)
    
    # Check if user is the leader
    if not group.is_leader(current_user.id):
        return jsonify({'error': 'Only the group leader can disband the group'}), 403
    
    # Verify group name in request
    data = request.get_json() or {}
    confirmed_name = data.get('name', '')
    
    if confirmed_name != group.name:
        return jsonify({'error': 'Group name does not match'}), 400
    
    group_name = group.name
    
    # Delete group (cascades to memberships and invites)
    db.session.delete(group)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{group_name} has been disbanded'
    }), 200


@bp.route('/api/groups/<int:group_id>/schedule-data')
@login_required
def get_group_schedule_data(group_id):
    """Get availability data for all group members"""
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member
    if not group.is_member(current_user.id):
        return jsonify({'error': 'You are not a member of this group'}), 403
    
    # Get query parameters
    start_slot = request.args.get('start_slot', type=int)
    end_slot = request.args.get('end_slot', type=int)
    
    if not start_slot or not end_slot:
        return jsonify({'error': 'start_slot and end_slot are required'}), 400
    
    # Get member IDs
    member_ids = [m.user_id for m in group.memberships.all()]
    
    if not member_ids:
        return jsonify({'slots': []}), 200
    
    # Query availability for all members
    slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.user_id.in_(member_ids),
        AvailabilitySlot.slot_index >= start_slot,
        AvailabilitySlot.slot_index <= end_slot
    ).all()
    
    # Group by slot_index and user
    result = {}
    for slot in slots:
        slot_idx = slot.slot_index
        if slot_idx not in result:
            result[slot_idx] = {}
        result[slot_idx][slot.user_id] = slot.state
    
    # Convert to list format with member count
    slots_list = []
    for slot_idx, user_states in result.items():
        available_count = sum(1 for state in user_states.values() if state == 2)
        slots_list.append({
            'slot_index': slot_idx,
            'user_states': user_states,
            'available_count': available_count,
            'total_members': len(member_ids)
        })
    
    return jsonify({'slots': slots_list}), 200


@bp.route('/api/invitations/pending')
@login_required
def get_pending_invitations():
    """Get pending invitations for current user"""
    # Expire old invites
    expire_old_invites()
    
    # Get pending invites within last 3 days
    cutoff = datetime.utcnow() - timedelta(days=3)
    invites = GroupInvite.query.filter(
        GroupInvite.invitee_id == current_user.id,
        GroupInvite.status == 'pending',
        GroupInvite.created_at >= cutoff
    ).all()
    
    return jsonify({
        'invites': [i.to_dict() for i in invites],
        'count': len(invites)
    }), 200
