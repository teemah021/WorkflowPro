# Django Approval System

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![DRF Version](https://img.shields.io/badge/DRF-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A production-ready Django-based approval workflow system with role-based access control, state management, and comprehensive audit logging.

## Problem Statement

Organizations need a secure, scalable system for managing approval workflows where:

- Users can submit requests
- Requests move through controlled states
- Authorized personnel can approve or reject requests
- Every action is traceable and auditable

## Architecture Overview

### Tech Stack

- **Backend**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL (UUID primary keys)
- **Authentication**: Session auth for admin, JWT for API
- **Server**: Gunicorn + Nginx
- **Containerization**: Docker & Docker Compose

### Core Components

```
approval_system/
├── apps/
│   ├── users/          # Custom user model with roles
│   ├── requests/       # Request models with state machine
│   ├── approvals/      # Business logic & API endpoints
│   ├── audit_logs/     # Append-only audit trail
│   └── notifications/  # (Future: Email/push notifications)
├── core/
│   ├── constants.py    # System-wide constants
│   ├── permissions.py  # Centralized permission classes
│   ├── exceptions.py   # Custom exception handling
│   └── middleware.py   # Custom middleware
└── config/
    ├── settings/       # Environment-specific configs
    └── urls.py         # URL routing
```

## Key Design Decisions

### 1. Custom User Model with Roles

Three role levels:

- **Admin**: Full system access
- **Manager**: Can approve assigned requests
- **User**: Can create and view own requests

### 2. State Machine for Requests

Valid transitions:

- `draft` → `submitted` (by creator)
- `submitted` → `approved` or `rejected` (by manager/admin)
- `approved` / `rejected` are terminal states

Invalid transitions raise exceptions server-side.

### 3. Audit Logging

Every meaningful action is logged:

- Actor (who)
- Action (what)
- Target object
- Timestamp
- IP address & user agent
- Metadata (context)

Logs are append-only and cannot be edited or deleted.

### 4. Security Considerations

- UUID primary keys (security, scalability)
- Soft deletes (data preservation)
- Server-side permission enforcement
- CSRF protection enabled
- HTTP-only cookies for sessions
- Rate limiting on auth endpoints
- No secrets in code (environment variables)
- Restricted CORS in production

## API Endpoints

### Authentication

- `POST /api/v1/users/` - Create user (admin only)
- `GET /api/v1/users/me/` - Get current user info

### Requests

- `GET /api/v1/requests/` - List requests (filtered by role)
- `POST /api/v1/requests/` - Create request
- `GET /api/v1/requests/{id}/` - Get request details
- `PUT /api/v1/requests/{id}/` - Update request (draft only)
- `DELETE /api/v1/requests/{id}/` - Soft delete request
- `POST /api/v1/requests/{id}/submit/` - Submit for approval
- `POST /api/v1/requests/{id}/approve/` - Approve request
- `POST /api/v1/requests/{id}/reject/` - Reject request

### Audit Logs

- `GET /api/v1/audit-logs/` - View audit logs (managers/admins)

## Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup:**

```bash
cd approval_system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Run migrations:**

```bash
python manage.py migrate
```

4. **Create superuser:**

```bash
python manage.py createsuperuser
```

5. **Run development server:**

```bash
python manage.py runserver
```

6. **Access the application:**

- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/

### Docker Deployment

```bash
# Start all services
docker-compose up --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.users
python manage.py test apps.requests

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## Database Schema

### Key Tables

**users**

- `id` (UUID, PK)
- `username`, `email`, `password`
- `role` (admin/manager/user)
- `is_deleted` (soft delete)
- Indexed: role, is_deleted

**requests**

- `id` (UUID, PK)
- `title`, `description`
- `status` (draft/submitted/approved/rejected)
- `creator_id` (FK to users)
- `assigned_to_id` (FK to users, nullable)
- `reviewed_by_id` (FK to users, nullable)
- `reviewed_at`, `rejection_reason`
- `is_deleted`
- Indexed: status, creator, assigned_to, is_deleted, created_at

**audit_logs**

- `id` (UUID, PK)
- `actor_id` (FK to users)
- `action` (create/update/approve/reject/etc)
- `content_type` & `object_id` (GenericForeignKey)
- `metadata` (JSON)
- `ip_address`, `user_agent`
- `timestamp`
- Indexed: actor+timestamp, action+timestamp, content_type+object_id

## Security Best Practices

**Implemented:**

- Environment-based configuration
- CSRF protection
- Secure cookies (HTTPS in prod)
- Rate limiting ready
- Soft deletes
- Audit logging
- Permission-based access control

**Production Checklist:**

- [ ] Set strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Set DEBUG=False
- [ ] Enable HTTPS/SSL
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Configure email backend
- [ ] Set up monitoring/logging
- [ ] Review and test all permissions

## Future Enhancements

- Email/push notifications
- Multi-tenant support
- Advanced search & filtering
- File attachments
- Request comments/discussion
- Bulk operations
- Workflow templates
- Analytics dashboard
- API rate limiting
- Celery for async tasks

## Interview Talking Points

### Architecture

- Clean separation of concerns
- Service layer pattern for business logic
- Centralized permission management
- Environment-specific settings

### Security

- Defense in depth approach
- Server-side validation & authorization
- Audit trail for accountability
- Soft deletes for data preservation

### Scalability

- UUID primary keys
- Database indexing strategy
- Stateless API design
- Docker containerization

### Code Quality

- Type hints where beneficial
- Comprehensive docstrings
- Unit tests for critical paths
- PEP 8 compliant

## License

This is a educational project. Use as you see fit.

## Contact

For questions or feedback about this project, please open an issue.
