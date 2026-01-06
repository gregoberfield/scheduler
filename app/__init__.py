from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import models
    from app.models import user, availability, group
    
    # Register blueprints
    from app.routes import auth, user as user_routes, availability as avail_routes, admin, group
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(avail_routes.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(group.bp)
    
    # Register main routes
    from app.routes import main
    app.register_blueprint(main.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
