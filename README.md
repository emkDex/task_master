# TaskMaster Pro

A production-ready, enterprise-grade Task Management REST API built with FastAPI and PostgreSQL.

## Features

- **User Management**: Registration, authentication with JWT tokens, profile management
- **Task Management**: Create, update, assign, track, and archive tasks
- **Team Collaboration**: Create teams, invite members, manage roles
- **Comments**: Discuss tasks with team members
- **File Attachments**: Upload and download task attachments
- **Notifications**: Real-time notifications via WebSocket
- **Activity Logging**: Comprehensive audit trail for all actions
- **Admin Dashboard**: Statistics and system-wide management

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TaskMaster Pro                           │
├─────────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI)                                            │
│  ├── Authentication (/api/v1/auth)                              │
│  ├── Users (/api/v1/users)                                      │
│  ├── Tasks (/api/v1/tasks)                                      │
│  ├── Teams (/api/v1/teams)                                      │
│  ├── Comments (/api/v1/tasks/{id}/comments)                     │
│  ├── Attachments (/api/v1/tasks/{id}/attachments)               │
│  ├── Notifications (/api/v1/notifications)                      │
│  ├── Activity Logs (/api/v1/activity)                           │
│  ├── Admin (/api/v1/admin)                                      │
│  └── WebSocket (/ws/{user_id})                                  │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer                                                  │
│  ├── AuthService                                                │
│  ├── TaskService                                                │
│  ├── TeamService                                                │
│  ├── NotificationService                                        │
│  ├── ActivityService                                            │
│  └── WebSocketManager                                           │
├─────────────────────────────────────────────────────────────────┤
│  CRUD Layer                                                     │
│  ├── CRUDBase (Generic)                                         │
│  ├── UserCRUD                                                   │
│  ├── TaskCRUD                                                   │
│  ├── TeamCRUD                                                   │
│  └── ...                                                        │
├─────────────────────────────────────────────────────────────────┤
│  Database Layer (SQLAlchemy 2.x Async)                          │
│  ├── PostgreSQL with asyncpg                                    │
│  ├── Alembic Migrations                                         │
│  └── UUID Primary Keys                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16+ with asyncpg
- **ORM**: SQLAlchemy 2.x (Async)
- **Migrations**: Alembic
- **Authentication**: JWT with python-jose
- **Password Hashing**: bcrypt via passlib
- **Validation**: Pydantic v2
- **Testing**: pytest with pytest-asyncio
- **Documentation**: OpenAPI/Swagger (auto-generated)

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (local or cloud)
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd taskmaster
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Setup

1. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

3. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `REFRESH_SECRET_KEY` | Refresh token signing key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | 7 |
| `ALLOWED_ORIGINS` | CORS origins (JSON array) | ["*"] |
| `DEBUG` | Debug mode | False |
| `MAX_FILE_SIZE_MB` | Max upload size | 10 |

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login (rate limited) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user |
| PUT | `/api/v1/users/me` | Update profile |
| PUT | `/api/v1/users/me/password` | Change password |
| GET | `/api/v1/users/` | List users (admin) |
| GET | `/api/v1/users/{id}` | Get user (admin) |
| DELETE | `/api/v1/users/{id}` | Deactivate user (admin) |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks` | List tasks (filtered, paginated) |
| POST | `/api/v1/tasks` | Create task |
| GET | `/api/v1/tasks/{id}` | Get task |
| PUT | `/api/v1/tasks/{id}` | Update task |
| DELETE | `/api/v1/tasks/{id}` | Archive task |
| POST | `/api/v1/tasks/{id}/assign` | Assign task |
| GET | `/api/v1/tasks/team/{team_id}` | List team tasks |

### Teams

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/teams` | Create team |
| GET | `/api/v1/teams` | List my teams |
| GET | `/api/v1/teams/{id}` | Get team |
| PUT | `/api/v1/teams/{id}` | Update team |
| DELETE | `/api/v1/teams/{id}` | Delete team |
| POST | `/api/v1/teams/{id}/members` | Add member |
| DELETE | `/api/v1/teams/{id}/members/{user_id}` | Remove member |
| PUT | `/api/v1/teams/{id}/members/{user_id}/role` | Update role |

### Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/{task_id}/comments` | List comments |
| POST | `/api/v1/tasks/{task_id}/comments` | Add comment |
| PUT | `/api/v1/tasks/{task_id}/comments/{id}` | Edit comment |
| DELETE | `/api/v1/tasks/{task_id}/comments/{id}` | Delete comment |

### Attachments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/{task_id}/attachments` | List attachments |
| POST | `/api/v1/tasks/{task_id}/attachments` | Upload file |
| GET | `/api/v1/tasks/{task_id}/attachments/{id}/download` | Download file |
| DELETE | `/api/v1/tasks/{task_id}/attachments/{id}` | Delete attachment |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications` | List notifications |
| GET | `/api/v1/notifications/unread-count` | Get unread count |
| PUT | `/api/v1/notifications/{id}/read` | Mark as read |
| PUT | `/api/v1/notifications/read-all` | Mark all as read |

### Activity Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/activity` | My activity |
| GET | `/api/v1/activity/task/{task_id}` | Task activity |
| GET | `/api/v1/activity/admin` | All activity (admin) |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/stats` | Dashboard statistics |
| GET | `/api/v1/admin/users` | All users |
| GET | `/api/v1/admin/tasks` | All tasks |
| GET | `/api/v1/admin/user-stats/{user_id}` | User statistics |

### WebSocket

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/{user_id}?token={jwt}` | Real-time notifications |

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "description"
```

### Run migrations

```bash
alembic upgrade head
```

### Rollback migrations

```bash
alembic downgrade -1
```

## Testing

### Run all tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=app --cov-report=html
```

### Run specific test file

```bash
pytest tests/test_auth.py
```

## Deployment

### Render

1. Create a new Web Service
2. Connect your repository
3. Set environment variables in Render dashboard
4. Build command: `pip install -r requirements.txt && alembic upgrade head`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Railway

1. Connect your repository to Railway
2. Add PostgreSQL plugin
3. Set environment variables
4. Deploy

### Fly.io

```bash
# Install flyctl and login
fly auth login

# Create app
fly launch

# Set secrets
fly secrets set DATABASE_URL=... SECRET_KEY=... REFRESH_SECRET_KEY=...

# Deploy
fly deploy
```

## Project Structure

```
taskmaster/
├── alembic/
│   ├── versions/          # Database migrations
│   ├── env.py             # Alembic configuration
│   └── alembic.ini        # Alembic settings
├── app/
│   ├── api/
│   │   └── v1/            # API routes
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings
│   │   ├── security.py    # JWT & passwords
│   │   ├── dependencies.py # FastAPI dependencies
│   │   └── exceptions.py  # Custom exceptions
│   ├── crud/              # CRUD operations
│   ├── db/                # Database setup
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── main.py            # Application entry
│   └── __init__.py
├── tests/                 # Test suite
├── uploads/               # File uploads
├── .env.example           # Environment template
├── docker-compose.yml     # Docker Compose config
├── Dockerfile             # Docker image
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Security Features

- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt
- Token rotation for refresh tokens
- Rate limiting on login endpoint
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- XSS protection through proper output encoding

## License

MIT License

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
