# Quick Start Guide

## Get Started in 5 Minutes

### Prerequisites

- Python 3.11+
- pip

### Step 1: Setup Environment

```bash
cd approval_system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install djangorestframework django-cors-headers
```

### Step 2: Run Migrations

```bash
python manage.py migrate
```

### Step 3: Create Sample Data

```bash
python manage.py create_sample_data
```

This creates:

- **admin** / admin123 (Admin role)
- **manager** / manager123 (Manager role)
- **user** / user123 (User role)
- Sample requests in various states

### Step 4: Start Server

```bash
python manage.py runserver
```

### Step 5: Explore the System

#### Access Admin Panel

1. Go to http://localhost:8000/admin/
2. Login with `admin` / `admin123`
3. Browse Users, Requests, and Audit Logs

#### Test the API

```bash
# Login as user
curl -c cookies.txt -X POST http://localhost:8000/admin/login/ \
  -d "username=user&password=user123"

# View your requests
curl -b cookies.txt http://localhost:8000/api/v1/requests/

# Create a new request
curl -b cookies.txt -X POST http://localhost:8000/api/v1/requests/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Request","description":"This is a test"}'
```

## Common Workflows

### As a User: Create and Submit Request

1. **Login** as user (user/user123)
2. **Create Request:**
   ```bash
   POST /api/v1/requests/
   {"title": "Budget Request", "description": "Need $5000 for marketing"}
   ```
3. **Submit for Approval:**
   ```bash
   POST /api/v1/requests/{id}/submit/
   ```

### As a Manager: Approve Request

1. **Login** as manager (manager/manager123)
2. **View assigned requests:**
   ```bash
   GET /api/v1/requests/
   ```
3. **Approve request:**
   ```bash
   POST /api/v1/requests/{id}/approve/
   ```

### As an Admin: View Everything

1. **Login** as admin (admin/admin123)
2. **View all requests** (all users)
3. **Check audit logs:**
   ```bash
   GET /api/v1/audit-logs/
   ```

## Explore Features

### State Machine

Try invalid transitions to see error handling:

```bash
# Try to approve a draft request (should fail)
POST /api/v1/requests/{draft-id}/approve/
```

### Permissions

Try unauthorized actions:

```bash
# Login as regular user
# Try to approve a request (should fail - permission denied)
POST /api/v1/requests/{id}/approve/
```

### Audit Logs

Every action is logged:

- Who performed it
- What they did
- When it happened
- IP address

## Database Schema

View in Django admin or check models:

- **Users:** `apps/users/models.py`
- **Requests:** `apps/requests/models.py`
- **Audit Logs:** `apps/audit_logs/models.py`

## Run Tests

```bash
python manage.py test
```

All tests should pass!

## Docker Alternative

If you prefer Docker:

```bash
docker-compose up --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py create_sample_data
```

Access at http://localhost:8000

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API details
3. Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture

## Troubleshooting

### Database Locked Error

```bash
rm db.sqlite3
python manage.py migrate
python manage.py create_sample_data
```

### Port Already in Use

```bash
python manage.py runserver 8001
```

### Import Errors

Make sure you're in the virtual environment:

```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

## Learning Path

1. **Explore Admin Panel** - See how data is organized
2. **Test API Endpoints** - Use curl or Postman
3. **Read the Code** - Start with `apps/users/models.py`
4. **Check Tests** - See `apps/*/tests.py` for examples
5. **Modify & Extend** - Add your own features!

## Pro Tips

- Use Django's browsable API at http://localhost:8000/api/v1/
- Check audit logs after every action
- Try different user roles to see permission differences
- Look at the code while using the system to understand flows
