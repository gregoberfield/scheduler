"""
Group models for WoW TBC party system.
Allows users to create 5-person groups with auto-generated names.
"""
from app import db
from datetime import datetime
from sqlalchemy import Index


class Group(db.Model):
    """5-person party group with auto-generated fun name"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    max_size = db.Column(db.Integer, default=5, nullable=False)
    
    # Relationships
    leader = db.relationship('User', foreign_keys=[leader_id], backref='led_groups')
    memberships = db.relationship('GroupMembership', back_populates='group', 
                                   cascade='all, delete-orphan', lazy='dynamic')
    invites = db.relationship('GroupInvite', back_populates='group',
                              cascade='all, delete-orphan', lazy='dynamic')
    
    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        """Convert group to dictionary"""
        members = self.memberships.all()
        return {
            'id': self.id,
            'name': self.name,
            'leader_id': self.leader_id,
            'leader_name': self.leader.character_name if self.leader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'max_size': self.max_size,
            'member_count': len(members),
            'is_full': len(members) >= self.max_size,
            'members': [m.to_dict() for m in members]
        }
    
    def is_member(self, user_id):
        """Check if user is a member of this group"""
        return self.memberships.filter_by(user_id=user_id).first() is not None
    
    def is_leader(self, user_id):
        """Check if user is the leader of this group"""
        return self.leader_id == user_id
    
    def is_full(self):
        """Check if group has reached max capacity"""
        return self.memberships.count() >= self.max_size
    
    def get_members(self):
        """Get list of User objects who are members"""
        from app.models.user import User
        member_ids = [m.user_id for m in self.memberships.all()]
        return User.query.filter(User.id.in_(member_ids)).all() if member_ids else []


class GroupMembership(db.Model):
    """Many-to-many relationship between groups and users"""
    __tablename__ = 'group_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    group = db.relationship('Group', back_populates='memberships')
    user = db.relationship('User', backref='group_memberships')
    
    # Ensure unique membership (user can't join same group twice)
    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='uq_group_user'),
        Index('idx_group_membership_group_user', 'group_id', 'user_id'),
    )
    
    def __repr__(self):
        return f'<GroupMembership group={self.group_id} user={self.user_id}>'
    
    def to_dict(self):
        """Convert membership to dictionary"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'user_name': self.user.character_name if self.user else None,
            'user_class': self.user.wow_class if self.user else None,
            'user_roles': self.user.get_roles() if self.user else [],
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }


class GroupInvite(db.Model):
    """Invitation to join a group"""
    __tablename__ = 'group_invites'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, accepted, declined, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    group = db.relationship('Group', back_populates='invites')
    inviter = db.relationship('User', foreign_keys=[inviter_id], backref='sent_invites')
    invitee = db.relationship('User', foreign_keys=[invitee_id], backref='received_invites')
    
    # Ensure unique invite (can't invite same user to same group multiple times)
    __table_args__ = (
        db.UniqueConstraint('group_id', 'invitee_id', name='uq_group_invitee'),
        Index('idx_group_invite_invitee_status', 'invitee_id', 'status'),
    )
    
    def __repr__(self):
        return f'<GroupInvite group={self.group_id} invitee={self.invitee_id} status={self.status}>'
    
    def to_dict(self):
        """Convert invite to dictionary"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'inviter_id': self.inviter_id,
            'inviter_name': self.inviter.character_name if self.inviter else None,
            'invitee_id': self.invitee_id,
            'invitee_name': self.invitee.character_name if self.invitee else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }
    
    def is_expired(self, days=7):
        """Check if invite is older than specified days"""
        if not self.created_at:
            return False
        age = datetime.utcnow() - self.created_at
        return age.days > days
