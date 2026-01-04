# Development Guide

## Project Overview

This is a Flask-based availability scheduling application for WoW TBC launch coordination. The architecture follows a standard Flask application pattern with:

- **Models**: SQLAlchemy ORM for database interactions
- **Routes**: Blueprint-based API endpoints and view handlers
- **Templates**: Jinja2 templates with Bootstrap 5 frontend
- **Static Assets**: jQuery for interactivity, custom CSS for styling

## Architecture

### Data Flow

1. **User Input** → Frontend (HTML/JS)
2. **AJAX Request** → Flask Route
3. **Route Handler** → Model/Database
4. **Database Response** → Route Handler
5. **JSON Response** → Frontend
6. **UI Update** → User sees changes

### Slot Index Calculation

Time slots are stored as integers calculated from Unix epoch:
```python
slot_index = unix_timestamp / 1800  # 1800 seconds = 30 minutes
```

This allows:
- Easy comparison and sorting
- Timezone-independent storage
- Efficient database indexing

### Aggregate Count Updates

When an AvailabilitySlot is created/updated/deleted, SQLAlchemy event listeners automatically update the AggregateSlotCount table. This provides fast heatmap queries without scanning all availability records.

## Key Components

### Models

**User** (`app/models/user.py`)
- Authentication and profile data
- First user auto-promoted to superuser
- Roles stored as JSON array

**AvailabilitySlot** (`app/models/availability.py`)
- Individual 30-minute availability blocks
- Unique constraint on (user_id, slot_index)
- States: 0=Unavailable, 1=Maybe, 2=Available

**AggregateSlotCount** (`app/models/availability.py`)
- Pre-calculated counts per slot
- Updated via SQLAlchemy event listeners
- Powers heatmap visualization

### Routes

**auth.py** - User signup, login, logout
**user.py** - Profile management API
**availability.py** - Availability CRUD operations
**admin.py** - User management and exports
**main.py** - Home page and static routes

### Frontend JavaScript

**availability_editor.js**
- Drag-and-drop slot selection
- Bulk update batching
- Timezone detection

**timeline.js**
- Multi-user timeline rendering
- Filtering and sorting
- Tooltip display

**heatmap.js**
- Aggregate visualization
- Intensity scaling
- Click-to-navigate

## Adding New Features

### Example: Add a "Notes" Field to Users

1. **Update Model** (`app/models/user.py`):
```python
notes = db.Column(db.Text, nullable=True)
```

2. **Update Form** (`app/templates/auth/signup.html`):
```html
<textarea name="notes" class="form-control"></textarea>
```

3. **Update Route** (`app/routes/auth.py`):
```python
user.notes = request.form.get('notes', '')
```

4. **Migrate Database**:
```bash
# For production, use Flask-Migrate
# For development, can drop and recreate:
rm scheduler.db
python init_db.py
```

### Example: Add Email Notifications

1. **Install Package**:
```bash
pip install Flask-Mail
echo "Flask-Mail==0.9.1" >> requirements.txt
```

2. **Configure** (`config.py`):
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
```

3. **Create Service** (`app/services/email.py`):
```python
from flask_mail import Mail, Message

mail = Mail()

def send_notification(user, subject, body):
    msg = Message(subject, recipients=[user.email])
    msg.body = body
    mail.send(msg)
```

4. **Use in Routes**:
```python
from app.services.email import send_notification

send_notification(user, "New Event", "...")
```

## Testing

### Manual Testing Checklist

- [ ] Sign up first user (becomes superuser)
- [ ] Sign up second user (regular member)
- [ ] Login/logout flows
- [ ] Set availability (drag-and-drop)
- [ ] View guild timeline with filters
- [ ] View heatmap
- [ ] Admin: promote user
- [ ] Admin: export roster CSV
- [ ] Mobile view (accordion)
- [ ] Timezone handling

### Unit Tests (TODO)

```python
# tests/test_auth.py
def test_first_user_is_superuser():
    user = User.query.first()
    assert user.is_superuser == True

# tests/test_availability.py
def test_slot_unique_constraint():
    # Try to create duplicate slot
    # Should raise IntegrityError
    pass
```

## Database Schema Changes

For production deployments, use Flask-Migrate:

```bash
pip install Flask-Migrate
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

For development, can recreate:
```bash
rm scheduler.db
python init_db.py
```

## Performance Optimization

### Current Optimizations

- Aggregate counts cached in database
- Indexes on user_id and slot_index
- Sticky headers prevent re-rendering
- AJAX for partial page updates

### Future Optimizations

- Redis for session storage
- PostgreSQL for better concurrency
- CDN for static assets
- WebSocket for real-time updates
- Database query result caching

## Security Considerations

### Implemented

✓ CSRF tokens on all forms
✓ Password hashing with bcrypt
✓ Rate limiting on sensitive endpoints
✓ Input sanitization with bleach
✓ Secure session cookies
✓ SQL injection prevention (ORM)

### Recommended for Production

- [ ] HTTPS only (configure nginx/Apache)
- [ ] Strong SECRET_KEY (32+ random bytes)
- [ ] Regular security updates
- [ ] Database backups
- [ ] Logging and monitoring
- [ ] Rate limiting at reverse proxy level
- [ ] Content Security Policy headers

## Deployment Checklist

### Development → Production

1. [ ] Set `FLASK_ENV=production`
2. [ ] Generate strong `SECRET_KEY`
3. [ ] Enable `SESSION_COOKIE_SECURE=True`
4. [ ] Configure HTTPS
5. [ ] Set up database backups
6. [ ] Configure logging
7. [ ] Set up monitoring (e.g., Sentry)
8. [ ] Use PostgreSQL instead of SQLite
9. [ ] Configure reverse proxy (nginx)
10. [ ] Set up systemd service
11. [ ] Configure firewall
12. [ ] Regular security updates

## Troubleshooting

### Common Issues

**"Table already exists" error**
```bash
rm scheduler.db
python init_db.py
```

**CSRF token errors**
- Check that templates include `{{ csrf_token() }}`
- Verify AJAX requests set `X-CSRFToken` header

**Availability not saving**
- Check browser console for errors
- Verify slot_index calculations
- Check rate limits

**Timeline not loading**
- Verify date range is valid
- Check filters aren't excluding all users
- Look for JavaScript errors in console

### Debug Mode

Enable detailed error messages:
```python
# config.py
DEBUG = True  # Only for development!
```

View SQL queries:
```python
# config.py
SQLALCHEMY_ECHO = True
```

## Code Style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Add docstrings to functions
- Keep functions focused and small
- Use type hints where helpful

## Contributing

When making changes:

1. Test locally first
2. Update documentation
3. Follow existing code patterns
4. Consider security implications
5. Test on mobile viewport

## Resources

- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Documentation: https://www.sqlalchemy.org/
- Bootstrap 5: https://getbootstrap.com/
- jQuery: https://jquery.com/

## Contact

For questions or issues, file an issue on GitHub or contact the development team.
