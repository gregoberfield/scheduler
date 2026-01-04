# WoW TBC Launch Availability Planner

A Flask-based web application for coordinating guild availability during The Burning Crusade launch. Players can set their availability across configurable date ranges using 30-minute time slots, visualize guild-wide availability, and help raid leaders identify optimal windows for group activities.

## Features

- **User Authentication** - Secure signup/login with character name, class, and password
- **Personal Availability** - Drag-and-drop interface to set Available/Maybe/Unavailable states
- **Guild Timeline** - View all characters' availability with filters and sorting
- **Heatmap View** - Visualize aggregate availability at a glance
- **Admin Panel** - User management and roster CSV export
- **Timezone Support** - Times stored in UTC, displayed in user's local timezone
- **Mobile Responsive** - Accordion view for mobile devices
- **Security** - CSRF protection, rate limiting, password hashing with bcrypt

## Tech Stack

- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Database**: SQLite (easily migrated to PostgreSQL)
- **Frontend**: Bootstrap 5, jQuery
- **Authentication**: Flask-Login, bcrypt
- **Security**: Flask-WTF (CSRF), Flask-Limiter, bleach

## Quick Start

### Prerequisites

- Python 3.11+
- pip
- (Optional) Docker & Docker Compose

### Installation

1. **Clone the repository**
   ```bash
   cd /home/greg/development/scheduler
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY to a random string
   ```

5. **Create class icons**
   ```bash
   chmod +x create_icons.sh
   ./create_icons.sh
   ```
   Or download official icons from Wowhead (see `app/static/img/classes/README.md`)

6. **Initialize database**
   ```bash
   python init_db.py
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

8. **Access the application**
   Open http://localhost:5000 in your browser

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Initialize database in container**
   ```bash
   docker-compose exec web python init_db.py
   ```

3. **Access the application**
   Open http://localhost:5000

## Usage

### First User (Superuser)

The first user to sign up automatically becomes a superuser with admin privileges.

### Setting Availability

1. Navigate to "My Availability"
2. Select a date range (defaults to next 7 days)
3. Choose selection mode (Available/Maybe/Unavailable)
4. Click and drag on the timeline grid to paint availability
5. Click "Save Changes"

### Viewing Guild Timeline

1. Navigate to "Guild Timeline"
2. Select date range and apply filters (class, role, confidence)
3. Hover over time slots to see who's available
4. Use sorting options to organize the view

### Admin Functions

Superusers and admins can:
- Promote members to admin status
- Export the roster as CSV
- View all user information

## Project Structure

```
scheduler/
├── app/
│   ├── models/          # Database models
│   │   ├── user.py
│   │   └── availability.py
│   ├── routes/          # API routes and views
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── availability.py
│   │   ├── admin.py
│   │   └── main.py
│   ├── static/          # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── img/classes/
│   ├── templates/       # Jinja2 templates
│   │   ├── auth/
│   │   ├── availability/
│   │   └── admin/
│   └── __init__.py
├── config.py            # Configuration
├── requirements.txt     # Python dependencies
├── run.py              # Application entry point
├── init_db.py          # Database initialization
├── Dockerfile          # Docker configuration
└── docker-compose.yml  # Docker Compose setup
```

## API Endpoints

### Authentication
- `POST /auth/api/signup` - Create new user
- `POST /auth/api/login` - Login
- `POST /auth/api/logout` - Logout

### User Profile
- `GET /api/me` - Get current user profile
- `PUT /api/me` - Update profile

### Availability
- `GET /api/availability` - Get availability with filters
- `POST /api/availability/bulk` - Bulk update slots
- `GET /api/availability/aggregate` - Get heatmap data

### Admin
- `GET /admin/api/users` - List all users
- `POST /admin/api/users/<id>/promote` - Promote to admin
- `POST /admin/api/users/<id>/demote` - Demote from admin
- `GET /admin/api/export/roster` - Download roster CSV

## Configuration

Environment variables (set in `.env`):

- `SECRET_KEY` - Flask secret key (required)
- `FLASK_ENV` - Environment (development/production)
- `DATABASE_URL` - Database connection string
- `SESSION_COOKIE_SECURE` - HTTPS-only cookies (True for production)
- `RATELIMIT_STORAGE_URL` - Rate limit storage backend

## Database Schema

### User
- Character name (unique username)
- WoW class (9 TBC classes)
- Roles (JSON array: tank/healer/dps)
- Password hash
- Timezone
- Superuser/Admin flags

### AvailabilitySlot
- User ID
- Slot index (Unix timestamp / 1800)
- State (0=Unavailable, 1=Maybe, 2=Available)
- Updated timestamp

### AggregateSlotCount
- Slot index
- Available count
- Maybe count
- Auto-updated on slot changes

## Development

### Running Tests
```bash
# TODO: Add test suite
pytest
```

### Database Migrations
To migrate from SQLite to PostgreSQL:
1. Update `DATABASE_URL` in `.env`
2. Run `init_db.py` to create tables
3. Export/import data as needed

## Production Deployment

1. Set `FLASK_ENV=production`
2. Generate strong `SECRET_KEY`
3. Enable `SESSION_COOKIE_SECURE=True`
4. Use HTTPS
5. Configure proper database backup
6. Consider using PostgreSQL for larger guilds
7. Use a reverse proxy (nginx/Apache) in front of Gunicorn

## Security Features

- ✓ CSRF protection on all forms
- ✓ Secure password hashing (bcrypt)
- ✓ Rate limiting (5 signups/hour, 100 availability updates/hour)
- ✓ Input sanitization with bleach
- ✓ HttpOnly and Secure cookies
- ✓ SQL injection protection (SQLAlchemy ORM)
- ✓ XSS protection (Jinja2 auto-escaping)

## Known Limitations

- SQLite may have concurrency limitations for very large guilds (>100 active users)
- No real-time updates (requires page refresh)
- Discord webhook integration not yet implemented (planned for future version)
- No proposal/event system (may be added later)

## Future Enhancements

- [ ] Discord webhook notifications
- [ ] Event proposal system with invitations
- [ ] Real-time updates with WebSockets
- [ ] Calendar export (iCal format)
- [ ] Mobile app
- [ ] Multiple guild support
- [ ] Advanced statistics and analytics

## Contributing

This is a guild-specific tool. Fork and customize as needed for your guild's requirements.

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please file an issue on the GitHub repository.

## Credits

Built for WoW TBC launch coordination. Class icons should be sourced from Wowhead or official Blizzard assets.
