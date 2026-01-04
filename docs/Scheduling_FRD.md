# Feature Requirements Document  
### WoW TBC Launch Availability Planner  
### *(Python + Flask + SQLite)*

---

## 1. Overview

### Purpose  
This application collects and visualizes player availability in **30‑minute time slots** across **multi‑day ranges** to help World of Warcraft players form groups for **The Burning Crusade** launch. The primary goal is to make overlapping availability easy to see so raid leaders can quickly identify optimal windows.

### Hard Requirements  
- **Python** as the programming language  
- **Flask** as the web framework
- **Bootstrap** as the web interface standard  
- **SQLite** as the database  
- **User authentication** with only:
  - Character name (used as username)
  - Class
  - Password

### Scope  
- Players select their own availability  
- Multi‑day scheduling  
- Times stored in UTC, displayed in each viewer’s local timezone  
- Character identity is the core user identity  
- Lightweight, easy to deploy, minimal dependencies  

---

## 2. Functional Requirements

### 2.1 User Authentication

#### Sign Up
- Required fields: **character name**, **class**, **password**
- Character name must be unique
- Password stored using secure hashing (bcrypt/Argon2)
- Successful signup logs the user in

#### Login
- Login with character name + password
- Secure session cookie
- Logout clears session

---

### 2.2 Availability Management

#### Set Availability
- Users select availability in **30‑minute slots**
- States:
  - **Available**
  - **Maybe**
  - **Unavailable** (default)
- Click‑and‑drag to set contiguous blocks
- Multi‑day range selection supported
- Availability stored in UTC slot indices

#### View Availability Timeline
- Horizontal timeline grid:
  - Rows = characters
  - Columns = 30‑minute slots
- Sticky date headers and day separators
- Hovering a slot shows:
  - List of available characters
  - Their classes/roles
- Top aggregate row shows:
  - Count of Available
  - Count of Maybe
  - Color intensity based on density

---

### 2.3 Filtering & Sorting

#### Filters
- Class
- Role (optional user preference)
- Timezone offset
- Availability confidence (Available only vs Available+Maybe)

#### Sorting
- Alphabetical
- Most available
- Class
- Timezone

---

### 2.4 Event Proposals

#### Create Proposal
- User selects a contiguous time window
- System displays:
  - Role coverage summary
  - List of available characters
- Organizer can define required roles (e.g., 2 tanks, 2 healers, 8 DPS)
- Proposal saved and notifications sent

#### Respond to Proposal
- Invited users can:
  - Accept
  - Decline
  - Tentative
- Responses stored and visible to organizer

---

### 2.5 Auto‑Suggestion Engine

- Given required roles, system suggests top N windows
- Ranking based on:
  - Number of Available players
  - Role coverage completeness
- Suggestions link directly to timeline preview

---

### 2.6 User Profile & Preferences

- Optional fields:
  - Role (tank/healer/dps)
  - Preferred raid times
  - Timezone override
- Preferences affect filtering and suggestions

---

## 3. Data Model

### 3.1 User
| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER PK | |
| character_name | TEXT UNIQUE | Used as username |
| class | TEXT | Predefined list |
| role | TEXT NULL | Optional |
| password_hash | TEXT | Secure hash |
| timezone | TEXT NULL | Optional override |
| created_at | TIMESTAMP | |

---

### 3.2 AvailabilitySlot
| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK | |
| slot_index | INTEGER | 30‑min bucket since epoch UTC |
| state | INTEGER | 0=Unavailable, 1=Maybe, 2=Available |
| updated_at | TIMESTAMP | |
| Unique constraint | (user_id, slot_index) | |

---

### 3.3 Proposal
| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER PK | |
| organizer_id | INTEGER FK | |
| start_slot | INTEGER | |
| end_slot | INTEGER | |
| required_roles | JSON | e.g. {"tank":2,"healer":2,"dps":8} |
| created_at | TIMESTAMP | |

---

### 3.4 ProposalResponse
| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER PK | |
| proposal_id | INTEGER FK | |
| user_id | INTEGER FK | |
| response | TEXT | accepted/declined/tentative |
| responded_at | TIMESTAMP | |

---

### 3.5 AggregateSlotCount (optional cache)
| Field | Type | Notes |
|-------|------|-------|
| slot_index | INTEGER PK | |
| available_count | INTEGER | |
| maybe_count | INTEGER | |

---

## 4. API Endpoints

### Authentication
- `POST /api/signup`
- `POST /api/login`
- `POST /api/logout`

### User Profile
- `GET /api/me`
- `PUT /api/me`

### Availability
- `GET /api/availability?start_slot=&end_slot=&filters=`
- `POST /api/availability/bulk`

### Proposals
- `POST /api/proposals`
- `POST /api/proposals/{id}/respond`
- `GET /api/suggestions?required_roles=...`

### Admin
- `GET /api/export/roster` (admin only)

---

## 5. UI Requirements

### Timeline Grid
- Rows: character name + class icon + role badge
- Columns: 30‑minute slots
- Color coding:
  - Green = Available
  - Yellow = Maybe
  - Gray = Unavailable
- Hover tooltips show:
  - Names
  - Classes
  - Roles
- Selection toolbar appears when user highlights a window

### Heatmap View
- Days × 30‑minute slots
- Color intensity = number of available players
- Clicking a cell jumps to timeline

### Mobile View
- Stacked availability bars per character
- Tap to expand into detailed timeline

---

## 6. Non‑Functional Requirements

### Performance
- Virtualized rendering for large rosters
- Bulk availability updates < 500ms
- Cached aggregate counts for heatmap

### Security
- Password hashing (bcrypt/Argon2)
- CSRF protection
- Secure cookies (HttpOnly, Secure)
- Input validation
- Rate limiting on signup & availability updates

### Scalability
- SQLite acceptable for small/medium guilds
- Schema designed to migrate to PostgreSQL if needed

### Accessibility
- Color + pattern + text labels
- Keyboard navigation
- ARIA labels for timeline cells

---

## 7. Deployment

- Dockerized Flask app
- Gunicorn for production
- SQLite stored on disk with backups
- Environment variables for secrets
- Optional background worker for notifications
