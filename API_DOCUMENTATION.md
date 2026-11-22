# API Documentation

## Base URL

```
http://localhost:8000/api/v1/
```

## Authentication

All endpoints require authentication using Django session authentication.

## Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message"
}
```

### Error Codes

- `PERMISSION_DENIED` - User lacks required permission
- `INVALID_STATE_TRANSITION` - Request cannot transition to requested state
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_FAILED` - Authentication credentials invalid

## Endpoints

### Users

#### Get Current User

```http
GET /api/v1/users/me/
```

**Response:**

```json
{
  "id": "uuid",
  "username": "john",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2026-01-20T10:00:00Z"
}
```

#### List Users

```http
GET /api/v1/users/
```

**Permission:** Admin only

#### Create User

```http
POST /api/v1/users/
```

**Permission:** Admin only

**Request:**

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "first_name": "New",
  "last_name": "User",
  "role": "user"
}
```

### Requests

#### List Requests

```http
GET /api/v1/requests/
```

**Returns:** Requests visible to the authenticated user based on their role

- **Admin:** All requests
- **Manager:** Own requests + assigned requests
- **User:** Only own requests

**Response:**

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Budget Approval",
      "description": "Q1 budget approval request",
      "status": "submitted",
      "status_display": "Submitted",
      "creator": {
        "id": "uuid",
        "username": "john",
        "email": "john@example.com",
        "role": "user"
      },
      "assigned_to": {
        "id": "uuid",
        "username": "manager",
        "role": "manager"
      },
      "reviewed_by": null,
      "reviewed_at": null,
      "rejection_reason": "",
      "created_at": "2026-01-20T10:00:00Z",
      "updated_at": "2026-01-20T10:05:00Z"
    }
  ]
}
```

#### Create Request

```http
POST /api/v1/requests/
```

**Request:**

```json
{
  "title": "New Request",
  "description": "Detailed description of the request"
}
```

**Response:** 201 Created with request object

#### Get Request Details

```http
GET /api/v1/requests/{id}/
```

#### Update Request

```http
PUT /api/v1/requests/{id}/
```

**Note:** Only works for requests in `draft` status
**Permission:** Request creator only

**Request:**

```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

#### Delete Request

```http
DELETE /api/v1/requests/{id}/
```

**Note:** Soft delete - only works for draft requests (or admin for any)
**Response:** 204 No Content

#### Submit Request for Approval

```http
POST /api/v1/requests/{id}/submit/
```

**Permission:** Request creator only
**Allowed from:** `draft` status only

**Response:**

```json
{
  "id": "uuid",
  "status": "submitted",
  "status_display": "Submitted",
  ...
}
```

#### Approve Request

```http
POST /api/v1/requests/{id}/approve/
```

**Permission:** Manager (assigned) or Admin
**Allowed from:** `submitted` status only

**Response:**

```json
{
  "id": "uuid",
  "status": "approved",
  "status_display": "Approved",
  "reviewed_by": {...},
  "reviewed_at": "2026-01-20T11:00:00Z",
  ...
}
```

#### Reject Request

```http
POST /api/v1/requests/{id}/reject/
```

**Permission:** Manager (assigned) or Admin
**Allowed from:** `submitted` status only

**Request:**

```json
{
  "reason": "Insufficient documentation provided"
}
```

**Response:**

```json
{
  "id": "uuid",
  "status": "rejected",
  "status_display": "Rejected",
  "reviewed_by": {...},
  "reviewed_at": "2026-01-20T11:00:00Z",
  "rejection_reason": "Insufficient documentation provided",
  ...
}
```

### Audit Logs

#### List Audit Logs

```http
GET /api/v1/audit-logs/
```

**Permission:** Manager (limited) or Admin (full)

**Response:**

```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "actor": {
        "id": "uuid",
        "username": "manager",
        "role": "manager"
      },
      "action": "approve",
      "action_display": "Approve",
      "content_type": 12,
      "object_id": "request-uuid",
      "metadata": {
        "old_status": "submitted",
        "new_status": "approved",
        "request_title": "Budget Approval"
      },
      "ip_address": "192.168.1.100",
      "timestamp": "2026-01-20T11:00:00Z"
    }
  ]
}
```

## State Transition Rules

### Valid Transitions

- `draft` → `submitted` (via `/submit/`)
- `submitted` → `approved` (via `/approve/`)
- `submitted` → `rejected` (via `/reject/`)

### Terminal States

- `approved` (no further transitions)
- `rejected` (no further transitions)

## Permission Matrix

| Action                 | User | Manager | Admin |
| ---------------------- | ---- | ------- | ----- |
| Create Request         | Yes  | Yes     | Yes   |
| View Own Requests      | Yes  | Yes     | Yes   |
| View Assigned Requests | No   | Yes     | Yes   |
| View All Requests      | No   | No      | Yes   |
| Edit Own Draft         | Yes  | Yes     | Yes   |
| Submit Request         | Yes  | Yes     | Yes   |
| Approve Request        | No   | Yes\*   | Yes   |
| Reject Request         | No   | Yes\*   | Yes   |
| View Audit Logs        | No   | Yes\*\* | Yes   |
| Manage Users           | No   | No      | Yes   |

\* Manager can only approve/reject assigned requests  
\*\* Manager can only see logs for requests they're involved in

## Testing the API

### Using curl

```bash
# Login (get session cookie)
curl -X POST http://localhost:8000/admin/login/ \
  -d "username=user&password=user123" \
  -c cookies.txt

# Create request
curl -X POST http://localhost:8000/api/v1/requests/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Request","description":"Test description"}'

# Submit request
curl -X POST http://localhost:8000/api/v1/requests/{id}/submit/ \
  -b cookies.txt

# Approve request (as manager)
curl -X POST http://localhost:8000/api/v1/requests/{id}/approve/ \
  -b manager-cookies.txt
```

### Using Python requests

```python
import requests

session = requests.Session()

# Login
session.post(
    'http://localhost:8000/admin/login/',
    data={'username': 'user', 'password': 'user123'}
)

# Create request
response = session.post(
    'http://localhost:8000/api/v1/requests/',
    json={
        'title': 'New Request',
        'description': 'Request description'
    }
)

request_id = response.json()['id']

# Submit request
session.post(f'http://localhost:8000/api/v1/requests/{request_id}/submit/')
```

## Rate Limiting

Currently not implemented but can be added using:

- `django-ratelimit` for view-level limiting
- Nginx rate limiting for request-level control

## Pagination

Default: 20 items per page

Query parameters:

- `?page=2` - Get page 2
- `?page_size=50` - Change page size (max 100)
