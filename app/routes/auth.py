from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models.user import User
import bleach

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def signup():
    """User signup"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        character_name = bleach.clean(request.form.get('character_name', '').strip())
        wow_class = request.form.get('wow_class', '')
        password = request.form.get('password', '')
        roles = request.form.getlist('roles')
        
        # Validation
        if not character_name or not wow_class or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(character_name=character_name).first():
            flash('Character name already exists.', 'danger')
            return render_template('auth/signup.html')
        
        # Create user
        user = User(
            character_name=character_name,
            wow_class=wow_class
        )
        user.set_password(password)
        user.set_roles(roles)
        
        # First user becomes superuser
        if User.query.count() == 0:
            user.is_superuser = True
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'Welcome, {character_name}!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('auth/signup.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        character_name = bleach.clean(request.form.get('character_name', '').strip())
        password = request.form.get('password', '')
        
        if not character_name or not password:
            flash('Both fields are required.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(character_name=character_name).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        else:
            flash('Invalid character name or password.', 'danger')
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# API endpoints for AJAX
@bp.route('/api/signup', methods=['POST'])
@limiter.limit("5 per hour")
def api_signup():
    """API endpoint for signup"""
    data = request.get_json()
    
    character_name = bleach.clean(data.get('character_name', '').strip())
    wow_class = data.get('wow_class', '')
    password = data.get('password', '')
    roles = data.get('roles', [])
    timezone = data.get('timezone', '')
    
    # Validation
    if not character_name or not wow_class or not password:
        return jsonify({'error': 'All fields are required'}), 400
    
    if User.query.filter_by(character_name=character_name).first():
        return jsonify({'error': 'Character name already exists'}), 400
    
    # Create user
    user = User(
        character_name=character_name,
        wow_class=wow_class,
        timezone=timezone
    )
    user.set_password(password)
    user.set_roles(roles)
    
    # First user becomes superuser
    if User.query.count() == 0:
        user.is_superuser = True
        user.is_admin = True
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 201


@bp.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login"""
    data = request.get_json()
    
    character_name = bleach.clean(data.get('character_name', '').strip())
    password = data.get('password', '')
    
    if not character_name or not password:
        return jsonify({'error': 'Both fields are required'}), 400
    
    user = User.query.filter_by(character_name=character_name).first()
    
    if user and user.check_password(password):
        login_user(user, remember=True)
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


@bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """API endpoint for logout"""
    logout_user()
    return jsonify({'success': True}), 200
