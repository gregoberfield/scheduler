from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin, db.Model):
    """User model representing a WoW character"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    character_name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    wow_class = db.Column(db.String(32), nullable=False)
    roles = db.Column(db.Text, nullable=True)  # JSON array of roles
    password_hash = db.Column(db.String(255), nullable=False)
    timezone = db.Column(db.String(64), nullable=True)
    is_superuser = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    availability_slots = db.relationship('AvailabilitySlot', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_roles(self):
        """Get roles as a list"""
        if self.roles:
            try:
                return json.loads(self.roles)
            except:
                return []
        return []
    
    def set_roles(self, roles_list):
        """Set roles from a list"""
        if roles_list:
            self.roles = json.dumps(roles_list)
        else:
            self.roles = None
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'character_name': self.character_name,
            'wow_class': self.wow_class,
            'roles': self.get_roles(),
            'timezone': self.timezone,
            'is_superuser': self.is_superuser,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.character_name}>'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))
