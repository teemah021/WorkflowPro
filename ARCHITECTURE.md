# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                   (Future: React/Vue)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       Nginx (Reverse Proxy)                  │
│              ├─ Static Files  ├─ Media Files                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Django REST Framework                  │    │
│  │         (Session Auth / JWT Tokens)                │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │              API Layer (ViewSets)                   │    │
│  │   - UserViewSet                                     │    │
│  │   - RequestViewSet                                  │    │
│  │   - AuditLogViewSet                                 │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │          Permission Layer (DRF Permissions)         │    │
│  │   - IsAdmin                                         │    │
│  │   - IsManager                                       │    │
│  │   - CanApproveRequest                              │    │
│  │   - CanViewOwnRequests                             │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │         Service Layer (Business Logic)              │    │
│  │   - RequestService                                  │    │
│  │     ├─ create_request()                            │    │
│  │     ├─ submit_request()                            │    │
│  │     ├─ approve_request()                           │    │
│  │     ├─ reject_request()                            │    │
│  │     └─ update_request()                            │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │            Model Layer (Django ORM)                 │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────────┐   │    │
│  │   │   User   │  │ Request  │  │  AuditLog    │   │    │
│  │   │  (UUID)  │  │  (UUID)  │  │   (UUID)     │   │    │
│  │   │          │  │          │  │              │   │    │
│  │   │ - role   │  │ - status │  │ - actor      │   │    │
│  │   │ - perms  │  │ - state  │  │ - action     │   │    │
│  │   └──────────┘  └──────────┘  │ - metadata   │   │    │
│  │                                 └──────────────┘   │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │          Middleware & Utilities                     │    │
│  │   - AuditMiddleware                                │    │
│  │   - Custom Exception Handler                       │    │
│  │   - Constants & Config                             │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                         │
│                                                              │
│   ┌─────────┐  ┌──────────┐  ┌────────────┐               │
│   │  users  │  │ requests │  │ audit_logs │               │
│   └─────────┘  └──────────┘  └────────────┘               │
│                                                              │
│   Indexes:                                                   │
│   - role, is_deleted                                        │
│   - status, creator, assigned_to                            │
│   - actor+timestamp, action+timestamp                       │
└─────────────────────────────────────────────────────────────┘
```

## Request Flow Diagram

### 1. Create and Submit Request

```
User (API Client)
      │
      │ POST /api/v1/requests/
      │ {"title": "...", "description": "..."}
      ▼
┌──────────────────┐
│  RequestViewSet  │ ◄─── Check Authentication
└────────┬─────────┘
         │ create()
         ▼
┌──────────────────┐
│ RequestService   │
│.create_request() │
└────────┬─────────┘
         │
         ├─ Create Request (status=DRAFT)
         │
         ├─ Log Action (AuditLog)
         │
         └─ Return Request Object
              │
              ▼
         Response 201 Created
```

### 2. Approve Request

```
Manager (API Client)
      │
      │ POST /api/v1/requests/{id}/approve/
      ▼
┌──────────────────┐
│  RequestViewSet  │ ◄─── Check Authentication
└────────┬─────────┘      Check IsManager/IsAdmin
         │ approve()      Check CanApproveRequest
         ▼
┌──────────────────┐
│ RequestService   │
│.approve_request()│
└────────┬─────────┘
         │
         ├─ Check Permission (manager/admin)
         │
         ├─ Check State (must be SUBMITTED)
         │
         ├─ Transition State (SUBMITTED → APPROVED)
         │
         ├─ Set reviewed_by & reviewed_at
         │
         ├─ Log Action (AuditLog)
         │   ├─ actor = manager
         │   ├─ action = APPROVE
         │   ├─ metadata = {old_status, new_status}
         │   ├─ ip_address
         │   └─ timestamp
         │
         └─ Return Updated Request
              │
              ▼
         Response 200 OK
```

## Data Flow & State Machine

```
Request Lifecycle:

┌──────────┐
│  DRAFT   │  ◄── Initial state
└────┬─────┘      (creator can edit)
     │
     │ submit() ◄── Creator only
     │
     ▼
┌──────────┐
│SUBMITTED │  ◄── Awaiting approval
└────┬─────┘      (cannot edit)
     │
     ├─────────────┬─────────────┐
     │             │             │
     │ approve()   │ reject()    │
     │ (manager)   │ (manager)   │
     │             │             │
     ▼             ▼             │
┌──────────┐  ┌──────────┐     │
│APPROVED  │  │REJECTED  │ ◄───┘
└──────────┘  └──────────┘
 (terminal)    (terminal)
```

## Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layers                        │
└─────────────────────────────────────────────────────────┘

Layer 1: Network
├─ HTTPS/TLS (Production)
├─ Nginx Rate Limiting
└─ CORS Policy

Layer 2: Authentication
├─ Session Authentication
├─ CSRF Tokens
└─ Secure Cookies (HTTP-only)

Layer 3: Authorization
├─ Role-Based Access (User/Manager/Admin)
├─ Permission Classes (DRF)
└─ Object-Level Permissions

Layer 4: Business Logic
├─ State Machine Validation
├─ Service Layer Checks
└─ Database Constraints

Layer 5: Data
├─ UUID Primary Keys
├─ Soft Deletes
└─ Audit Trail (Append-Only)

Layer 6: Code
├─ Input Validation
├─ SQL Injection Protection (ORM)
└─ XSS Prevention
```

## Deployment Architecture

```
Production Environment:

┌──────────────────────────────────────────────────────┐
│                   Load Balancer                       │
│                  (Optional/Future)                    │
└───────────────────────┬──────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Nginx 1    │  │  Nginx 2    │  │  Nginx 3    │
│  (Reverse   │  │  (Reverse   │  │  (Reverse   │
│   Proxy)    │  │   Proxy)    │  │   Proxy)    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Gunicorn 1  │  │ Gunicorn 2  │  │ Gunicorn 3  │
│  Django     │  │  Django     │  │  Django     │
│  Workers    │  │  Workers    │  │  Workers    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   PostgreSQL Primary          │
        │   (Master)                    │
        └────────┬──────────────────────┘
                 │
                 │ Replication
                 ▼
        ┌───────────────────────────────┐
        │   PostgreSQL Replica          │
        │   (Read-Only)                 │
        └───────────────────────────────┘
```

## Component Responsibilities

### API Layer (ViewSets)

- HTTP request/response handling
- Input deserialization
- Output serialization
- Route delegation

### Permission Layer

- Authentication check
- Role verification
- Object-level access control
- Permission inheritance

### Service Layer

- Business logic execution
- State transition enforcement
- Cross-cutting concerns (audit)
- Transaction management

### Model Layer

- Data structure definition
- Database constraints
- Query optimization
- Soft delete handling

### Audit System

- Action logging
- Metadata capture
- IP tracking
- Immutable records

## Technology Stack

```
Frontend (Future)
  └─ React/Vue + Axios

Backend
  ├─ Django 5.0+
  ├─ Django REST Framework 3.14+
  ├─ Python 3.11+
  └─ Gunicorn (WSGI)

Database
  ├─ PostgreSQL 15+
  └─ UUID Primary Keys

Infrastructure
  ├─ Docker & Docker Compose
  ├─ Nginx (Reverse Proxy)
  └─ Linux (Ubuntu/Debian)

Development
  ├─ pytest (Testing)
  ├─ black (Code Formatting)
  └─ flake8 (Linting)

Optional
  ├─ Redis (Caching/Celery)
  ├─ Celery (Async Tasks)
  └─ Sentry (Error Tracking)
```

## Scalability Considerations

### Horizontal Scaling

- Stateless application design
- Session storage in database/Redis
- Load balancer ready

### Database Optimization

- UUID primary keys (distributed systems)
- Strategic indexing
- Query optimization
- Connection pooling

### Caching Strategy (Future)

- Redis for session storage
- Cache frequently accessed data
- Invalidation on updates

### Async Processing (Optional)

- Celery for email notifications
- Background task processing
- Scheduled jobs
