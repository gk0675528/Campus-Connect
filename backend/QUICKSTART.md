"""Quick Start Guide

## Prerequisites
- Python 3.10 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- Git

## Setup Instructions

### 1. Clone Repository
```bash
git clone <repository-url>
cd backend
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\\Scripts\\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Start Services
```bash
# PostgreSQL (if running locally)
# Windows: 
pg_ctl -D "C:\\Program Files\\PostgreSQL\\data" start

# macOS (if installed via Homebrew):
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# Redis
redis-server

# Or using Docker:
docker-compose up -d
```

### 6. Initialize Database
```bash
# Create tables
python -c "from core.config.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 7. Run Application
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Sample Requests

### Register User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "password": "password"
  }'
```

### Search Mentors
```bash
curl -X GET "http://localhost:8000/api/mentors/search?limit=10" \\
  -H "Content-Type: application/json" \\
  -d '{
    "skills": ["Python", "Web Development"]
  }'
```

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Database Connection Error
- Check if PostgreSQL is running
- Verify DATABASE_URL in .env
- Check credentials

### Redis Connection Error
- Check if Redis is running
- Verify REDIS_URL in .env

## Development Tips

### Run Tests
```bash
pytest
```

### Format Code
```bash
black .
```

### Lint Code
```bash
pylint modules/
```

### Database Migrations (with Alembic)
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Project Structure Reference
- `/core` - Configuration, middleware, exceptions
- `/modules` - Feature modules
- `/integrations` - Third-party integrations
- `/storage` - File storage
- `/websocket` - WebSocket functionality

## Next Steps

1. Create your first user
2. Explore API documentation at `/docs`
3. Check database schema
4. Start building features

## Support

For issues and questions:
1. Check the documentation at `/docs/api_docs/README.md`
2. Review the code structure
3. Check error logs in `logs/`

## License

MIT License
"""
