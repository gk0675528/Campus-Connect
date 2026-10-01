# Campus Connect - Database Setup & Verification Guide

## Overview

This application uses:
- **Primary Database**: PostgreSQL 15+ with async SQLAlchemy + asyncpg
- **Cache**: Redis 7+
- **Document Store**: MongoDB 7+ (optional)
- **Migration Tool**: Alembic

---

## 1. Database Connection Configuration

### Local Development Setup

#### Option A: Docker Compose (Recommended)

```bash
cd backend

# 1. Create .env from example
cp .env.example .env

# 2. Set PostgreSQL password
export POSTGRES_PASSWORD=your_secure_password_here
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# 3. Start all services
docker-compose up -d

# 4. Verify services are healthy
docker-compose ps
```

**Expected output:**
```
CONTAINER ID   STATUS
campusconnect-db       Up (healthy)
campusconnect-redis    Up (healthy)
campusconnect-mongodb  Up (healthy)
campusconnect-api      Up
```

#### Option B: Manual Local PostgreSQL

**Prerequisites:**
```bash
# macOS
brew install postgresql redis mongodb-community

# Ubuntu/Debian
sudo apt-get install postgresql redis-server

# Start services
brew services start postgresql  # macOS
brew services start redis       # macOS
sudo systemctl start postgresql # Linux
sudo systemctl start redis-server # Linux
```

**Create database:**
```bash
sudo -u postgres psql

# In PostgreSQL shell:
CREATE USER campusconnect WITH PASSWORD 'your_password';
CREATE DATABASE campusconnect OWNER campusconnect;
GRANT ALL PRIVILEGES ON DATABASE campusconnect TO campusconnect;
\q
```

**Update .env:**
```bash
cp .env.example .env

# Edit .env
DATABASE_URL=postgresql+asyncpg://campusconnect:your_password@localhost:5432/campusconnect
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=your_generated_secret_key
```

---

## 2. Environment Variables

### Required Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://user:pass@localhost:5432/campusconnect` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | `<64-char random string>` |

### Connection String Format

```
postgresql+asyncpg://username:password@host:port/database?sslmode=prefer
```

**For Production (with SSL):**
```
postgresql+asyncpg://username:password@host.region.aws.neon.tech/database?sslmode=require
```

### Critical Settings

```python
# backend/core/config/settings.py

# Database
DATABASE_URL: str = os.getenv("DATABASE_URL")
DATABASE_ECHO: bool = DEBUG  # SQL logging in debug mode

# Redis
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Security
SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")  # MUST be set in production
```

---

## 3. Database Initialization & Migrations

### Alembic Migration Flow

```
┌─────────────────────────────────────┐
│  First Deployment (Fresh Database)  │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  $ alembic upgrade head             │
│  - Creates all tables from migration│
│  - Records migration version        │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  $ python main.py                   │
│  - FastAPI starts                   │
│  - init_db() seeds sample data      │
│  - App ready for requests           │
└─────────────────────────────────────┘
```

### Migration Commands

```bash
cd backend

# 1. Run migrations (creates/updates schema)
alembic upgrade head

# 2. Check migration status
alembic current
alembic history

# 3. Create a new migration (after model changes)
alembic revision --autogenerate -m "description"

# 4. Rollback (WARNING: deletes tables)
alembic downgrade base

# 5. Rollback to previous migration
alembic downgrade -1
```

### Initial Migration Contents

**File:** `backend/alembic/versions/a7f4b3b8872b_initial_schema.py`

**Creates these tables:**
```
users
├── Columns: 28 (id, email, username, profile info, mentor fields, OAuth, timestamps)
├── Indexes: ix_users_email (unique), ix_users_username (unique), ix_users_mentor_search
└── Foreign Keys: None (root table)

communities
├── Columns: 11
├── Foreign Key: creator_id → users.id
└── Unique Index: name

sessions (✅ FIXED)
├── Columns: 22 (includes idempotency_key)
├── Unique Constraint: (student_id, idempotency_key)
├── Check Constraint: student_rating >= 1 AND <= 5
├── Composite Index: (mentor_id, status, scheduled_at)
└── Foreign Keys: mentor_id, student_id → users.id

posts, comments, messages, notifications, payments, wallets, verification_requests
community_members, mentor_connections, post_upvotes (association tables)

profiles (✅ NEW)
├── Columns: 24 (extended user profile)
├── Foreign Key: user_id → users.id (unique)
└── Unique Constraint: user_id
```

---

## 4. Database Connection Testing

### Test 1: Environment Setup

```bash
cd backend
python -c "
from core.config.settings import settings
print(f'DATABASE_URL: {settings.DATABASE_URL}')
print(f'REDIS_URL: {settings.REDIS_URL}')
print(f'Secret Key Present: {bool(settings.SECRET_KEY)}')
print(f'Environment: {settings.ENVIRONMENT}')
"
```

**Expected output:**
```
DATABASE_URL: postgresql+asyncpg://campusconnect:***@localhost:5432/campusconnect
REDIS_URL: redis://localhost:6379/0
Secret Key Present: True
Environment: development
```

### Test 2: Direct PostgreSQL Connection

```bash
# Using psql
psql -U campusconnect -h localhost -d campusconnect -c "SELECT version();"

# Expected: PostgreSQL 15.x on...
```

### Test 3: SQLAlchemy Engine Test

```bash
cd backend
python -c "
import asyncio
from core.config.database import engine

async def test():
    try:
        async with engine.begin() as conn:
            result = await conn.execute('SELECT 1')
            print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Connection failed: {e}')

asyncio.run(test())
"
```

### Test 4: Alembic Migration Test

```bash
cd backend

# Check current migration status
alembic current
# Expected: a7f4b3b8872b_initial_schema

# Verify migration against database
alembic upgrade head --sql | head -50
# Shows the SQL that will be executed
```

### Test 5: Verify Tables Created

```bash
# Via psql
psql -U campusconnect -h localhost -d campusconnect -c "
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
"

# Expected tables:
# alembic_version
# comments
# communities
# community_members
# mentor_connections
# messages
# notifications
# payments
# post_upvotes
# posts
# profiles (✅ NEW)
# sessions
# users
# verification_requests
# wallets
```

### Test 6: Verify Constraints & Indexes

```bash
psql -U campusconnect -h localhost -d campusconnect -c "
-- Check sessions table structure
\d sessions

-- Expected:
-- - idempotency_key column (character varying)
-- - Constraints: uq_sessions_student_idempotency, ck_sessions_student_rating_range
-- - Index: ix_sessions_mentor_status_schedule
"

# Verify profiles table
psql -U campusconnect -h localhost -d campusconnect -c "\d profiles"
```

### Test 7: Test Foreign Keys

```bash
psql -U campusconnect -h localhost -d campusconnect -c "
SELECT 
  constraint_name,
  table_name,
  column_name
FROM information_schema.key_column_usage 
WHERE constraint_type = 'FOREIGN KEY' 
AND table_name IN ('sessions', 'posts', 'profiles')
ORDER BY table_name;
"

# Expected:
# sessions → mentor_id, student_id → users.id
# posts → author_id, community_id
# comments → post_id, author_id
# profiles → user_id → users.id
```

### Test 8: Redis Connection

```bash
# Using redis-cli
redis-cli -h localhost ping
# Expected: PONG

# Check Redis is accessible
redis-cli -h localhost INFO server
```

### Test 9: Full Application Startup

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
alembic upgrade head

# 3. Start the application
python main.py

# Expected console output:
# INFO: Starting CampusConnect API
# INFO: Database initialized
# INFO: Redis connected
# INFO: MongoDB document store initialized
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### Test 10: Health Check Endpoint

```bash
# In another terminal
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "1.1.0", "document_store": "connected"}
```

---

## 5. Common Database Issues & Solutions

### Issue 1: "Connection refused" on localhost:5432

**Symptoms:**
```
asyncpg.connection.PostgresError: could not connect to the server: 
Connection refused. Is the server running on host "localhost" 
(127.0.0.1) port 5432?
```

**Solutions:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres        # Docker
psql -U postgres                 # Local

# Restart PostgreSQL
docker-compose restart postgres  # Docker
brew services restart postgresql # macOS
sudo systemctl restart postgresql # Linux

# Verify connection details
echo $DATABASE_URL
# Should be: postgresql+asyncpg://campusconnect:password@localhost:5432/campusconnect
```

### Issue 2: "FATAL: database does not exist"

**Symptoms:**
```
psycopg2.errors.InvalidCatalogName: database "campusconnect" does not exist
```

**Solutions:**
```bash
# Create database via docker-compose
docker-compose exec postgres psql -U campusconnect -c "CREATE DATABASE campusconnect;"

# Or manually
sudo -u postgres psql -c "CREATE DATABASE campusconnect OWNER campusconnect;"
```

### Issue 3: "Authentication failed"

**Symptoms:**
```
psycopg2.OperationalError: could not translate host name "localhost" to address: 
Name or service not known
```

**Solutions:**
```bash
# Verify credentials in .env
grep DATABASE_URL backend/.env

# Test connection with psql
psql -U campusconnect -h localhost -d campusconnect -W
# Enter password

# For Docker, ensure network connectivity
docker network inspect campusconnect-network
```

### Issue 4: "Alembic migration fails"

**Symptoms:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn: 
column "idempotency_key" does not exist
```

**Solutions:**
```bash
# 1. Verify migration file is updated
cat backend/alembic/versions/a7f4b3b8872b_initial_schema.py | grep idempotency_key

# 2. Downgrade and re-apply (DEVELOPMENT ONLY)
alembic downgrade base
alembic upgrade head

# 3. Verify migration status
alembic current
alembic history

# 4. If stuck, manually reset (dev only)
docker-compose exec postgres dropdb -U campusconnect campusconnect
docker-compose exec postgres createdb -U campusconnect campusconnect
alembic upgrade head
```

### Issue 5: "Relations not visible to Alembic"

**Symptoms:**
```
Target database is not up to date
```

**Solutions:**
```bash
# Ensure all models are imported
grep -r "import.*models" backend/alembic/env.py

# Should include both:
# from modules.users import models
# from modules.profiles.models import profile

# Regenerate migration if models changed
alembic revision --autogenerate -m "add new column"
```

---

## 6. Production Deployment

### Pre-Deployment Checklist

- [ ] Database URL uses PostgreSQL (not SQLite)
- [ ] PostgreSQL version ≥ 12
- [ ] asyncpg driver is available
- [ ] SECRET_KEY is set (min 32 chars, not a placeholder)
- [ ] REDIS_URL is accessible
- [ ] DATABASE_URL connection tested
- [ ] SSL/TLS configured if required
- [ ] Database backups enabled
- [ ] Alembic migrations run before app start

### Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Run migrations (BEFORE starting app)
alembic upgrade head

# 4. Check migration status
alembic current

# 5. Start application
uvicorn main:app --host 0.0.0.0 --port 8000

# OR with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Docker Production Deployment

**Dockerfile (updated):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations then start app
CMD ["sh", "-c", "alembic upgrade head && python main.py"]
```

### Environment Variables (Production)

```bash
DATABASE_URL=postgresql+asyncpg://campusconnect:SECURE_PASSWORD@prod-db.region.aws.neon.tech:5432/campusconnect?sslmode=require
REDIS_URL=redis://:REDIS_PASSWORD@prod-redis.region.cache.amazonaws.com:6379/0
SECRET_KEY=<64-character-random-string>
DEBUG=False
ENVIRONMENT=production
```

---

## 7. Monitoring & Maintenance

### Check Database Health

```bash
# Connection pool stats
psql -U campusconnect -h localhost -d campusconnect -c "
SELECT datname, count(*) as connections 
FROM pg_stat_activity 
GROUP BY datname;
"

# Table sizes
psql -U campusconnect -h localhost -d campusconnect -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Slow queries (requires log_min_duration_statement set)
psql -U campusconnect -h localhost -d campusconnect -c "
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
"
```

### Regular Backups

```bash
# Backup database
pg_dump -U campusconnect -h localhost campusconnect > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
psql -U campusconnect -h localhost campusconnect < backup_20240101_120000.sql
```

### Migration History

```bash
# View all migrations
alembic history

# View current migration
alembic current

# Detailed revision info
alembic show a7f4b3b8872b_initial_schema
```

---

## 8. Troubleshooting Checklist

```bash
# 1. Verify all services running
docker-compose ps

# 2. Check database connectivity
psql -U campusconnect -h localhost -d campusconnect -c "SELECT 1;"

# 3. Verify migration status
alembic current

# 4. Check table creation
psql -U campusconnect -h localhost -d campusconnect -c "\dt"

# 5. Verify constraints
psql -U campusconnect -h localhost -d campusconnect -c "
  SELECT constraint_name, table_name 
  FROM information_schema.table_constraints 
  WHERE constraint_type = 'UNIQUE';"

# 6. Test Redis
redis-cli -h localhost ping

# 7. Start app with debug logging
DEBUG=True python main.py

# 8. Check app logs
docker-compose logs api

# 9. Verify environment variables
python -c "from core.config.settings import settings; print(vars(settings))"

# 10. Test migrations roll-forward/backward
alembic downgrade -1 --sql  # Preview
alembic downgrade -1        # Apply
alembic upgrade +1          # Restore
```

---

## Summary

✅ **Database Setup Complete When:**
1. PostgreSQL is running and accessible
2. Database `campusconnect` exists
3. User `campusconnect` has permissions
4. Alembic migration ran successfully (`alembic upgrade head`)
5. All 15 tables created with correct schema
6. Foreign keys and constraints in place
7. Redis connected
8. Application starts without errors
9. `/health` endpoint returns `{"status": "healthy", ...}`

