# Skillora

Skillora is a student learning, mentorship, and career growth platform that connects students with mentors, alumni, educators, and learning communities. The project contains a FastAPI backend and a static HTML/CSS/JavaScript frontend.

> Learn Better. Connect Smarter. Grow Together.

## Contents

- [CampusConnect](#campusconnect)
  - [Contents](#contents)
  - [Overview](#overview)
    - [Backend](#backend)
    - [Frontend](#frontend)
  - [Architecture](#architecture)
  - [Repository Structure](#repository-structure)
  - [Requirements](#requirements)
  - [Local Development](#local-development)
    - [1. Configure the backend](#1-configure-the-backend)
    - [2. Create a Python environment](#2-create-a-python-environment)
    - [3. Start PostgreSQL and Redis](#3-start-postgresql-and-redis)
    - [4. Initialize the database](#4-initialize-the-database)
    - [5. Start the API](#5-start-the-api)
    - [6. Start the frontend](#6-start-the-frontend)
  - [Docker Development](#docker-development)
  - [Frontend Configuration](#frontend-configuration)
  - [Backend Configuration](#backend-configuration)
  - [Application Features](#application-features)
    - [Available application areas](#available-application-areas)
    - [Feature flags](#feature-flags)
  - [API Surface](#api-surface)
  - [Authentication](#authentication)
  - [Database and Migrations](#database-and-migrations)
  - [Testing and Validation](#testing-and-validation)
  - [Production Deployment](#production-deployment)
    - [Required production settings](#required-production-settings)
    - [Deployment sequence](#deployment-sequence)
  - [Troubleshooting](#troubleshooting)
    - [Browser reports a network or CORS error](#browser-reports-a-network-or-cors-error)
    - [API fails during startup](#api-fails-during-startup)
    - [Docker API does not start](#docker-api-does-not-start)
    - [Login redirects immediately](#login-redirects-immediately)
  - [Security Checklist](#security-checklist)
  - [Project Status](#project-status)
  - [License](#license)

## Overview

### Backend

The backend is an asynchronous FastAPI service with:

- PostgreSQL and SQLAlchemy for persistence
- Redis for caching and runtime coordination
- JWT authentication and role-aware access control
- Request logging, audit logging, and rate limiting middleware
- Stripe and Razorpay integration points
- Google and LinkedIn OAuth integration points
- Optional OpenAI and S3 integration points
- Swagger and ReDoc API documentation

### Frontend

The frontend is a static web application built with:

- HTML5, CSS3, and vanilla JavaScript
- Bootstrap 5 and Bootstrap Icons from CDNs
- A centralized Fetch API client in `campusconnect-frontend/js/api.js`
- Shared runtime configuration in `campusconnect-frontend/js/config.js`
- JWT session handling in `campusconnect-frontend/js/auth.js`
- Separate pages for authentication, dashboards, mentors, bookings, communities, messaging, payments, notifications, profiles, settings, and administration

## Architecture

```text
Browser
  |
  | HTTPS / JSON / Bearer JWT
  v
Static Frontend ---------------------> FastAPI API
                                         |
                                         +--> PostgreSQL
                                         +--> Redis
                                         +--> Stripe / Razorpay
                                         +--> OAuth providers
                                         +--> OpenAI (optional)
                                         +--> S3 (optional)
```

The frontend sends requests to `/api/...` endpoints through the centralized `API` client. The client automatically serializes JSON request bodies, attaches the access token, parses FastAPI errors, and handles expired sessions.

## Repository Structure

```text
.
├── backend/
│   ├── main.py                       # FastAPI application entry point
│   ├── requirements.txt               # Python dependencies
│   ├── pyproject.toml                 # Python project tooling
│   ├── .env.example                   # Backend environment template
│   ├── Dockerfile                     # Backend container image
│   ├── docker-compose.yml              # PostgreSQL, Redis, and API services
│   ├── alembic/                       # Database migration configuration
│   ├── app/api.py                     # API router aggregation
│   ├── core/                          # Settings, security, database, middleware
│   ├── modules/                       # Domain modules and API routes
│   ├── integrations/                  # OAuth and payment clients
│   ├── database/seeders/              # Seed data utilities
│   ├── storage/                       # S3 integration
│   ├── websocket/                     # Chat WebSocket support
│   └── docs/api_docs/                 # Backend API notes
├── campusconnect-frontend/
│   ├── index.html                     # Public landing page
│   ├── login.html                     # Login page
│   ├── register.html                  # Registration page
│   ├── dashboard.html                 # Student dashboard
│   ├── mentors.html                   # Mentor discovery
│   ├── bookings.html                  # Booking management
│   ├── communities.html               # Community discovery
│   ├── messages.html                  # Direct messaging
│   ├── payments.html                  # Payment flow
│   ├── notifications.html             # Notifications
│   ├── profile.html                   # Profile management
│   ├── settings.html                  # Account settings
│   ├── mentor-dashboard.html          # Mentor portal
│   ├── admin-dashboard.html           # Admin portal
│   ├── css/                           # Shared and page styles
│   ├── js/                            # API, auth, UI, and page modules
│   └── assets/                        # Logos and images
└── README.md                          # This guide
```

## Requirements

For local development:

- Python 3.10 or newer
- PostgreSQL 12 or newer
- Redis 6 or newer
- A modern browser
- Docker Desktop and Docker Compose are recommended for local infrastructure

Node.js is not required by the current static frontend. A static HTTP server is required because browser requests from `file://` pages are restricted.

## Local Development

### 1. Configure the backend

```powershell
cd backend
Copy-Item .env.example .env
```

Edit `.env` and set at least:

```text
DEBUG=True
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/campusconnect
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=replace-with-a-long-random-value
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000
```

On macOS or Linux, use `cp .env.example .env` instead of `Copy-Item`.

### 2. Create a Python environment

Windows PowerShell:
\
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start PostgreSQL and Redis

Start both services locally, or use the Docker instructions below. Confirm that the credentials in `DATABASE_URL` match PostgreSQL.

### 4. Initialize the database

```bash
python -c "from core.config.database import init_db; import asyncio; asyncio.run(init_db())"
```

For an existing migration history:

```bash
alembic upgrade head
```

### 5. Start the API

Keep this terminal open while the backend is running. It stays alive until you stop it with `Ctrl+C`.

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On Windows PowerShell:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend is available at:

- API root: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 6. Start the frontend

Open a second terminal from the repository root:

```bash
cd campusconnect-frontend
python -m http.server 3000
```

Open `http://localhost:3000` in a browser. The default frontend API target is `http://localhost:8000`.

## Docker Development

Docker Compose starts PostgreSQL, Redis, and the backend API:

```bash
cd backend
$env:SECRET_KEY = "local-development-secret-change-me"
docker compose up --build
```

On macOS or Linux:

```bash
cd backend
export SECRET_KEY="local-development-secret-change-me"
docker compose up --build
```

The Compose file exposes:

- PostgreSQL on port `5432`
- Redis on port `6379`
- FastAPI on port `8000`

The frontend remains a static site and can be served separately on port `3000`:

```bash
cd campusconnect-frontend
python -m http.server 3000
```

Stop containers with:

```bash
docker compose down
```

Add `-v` only when you intentionally want to delete the local PostgreSQL and Redis volumes.

## Frontend Configuration

The frontend configuration is centralized in `campusconnect-frontend/js/config.js`.

Resolution order for the API URL:

1. Existing `window.APP_CONFIG.API_BASE_URL`
2. `window.CAMPUSCONNECT_API_URL`
3. The current browser origin when served over HTTP or HTTPS
4. `http://localhost:8000` when opened as a local file

For a separate production frontend and backend, define the API URL before loading `js/config.js` in each deployed page, or update the deployment copy of the configuration script:

```html
<script>
  window.CAMPUSCONNECT_API_URL = "https://api.example.com";
</script>
<script src="js/config.js"></script>
```

The frontend must be served over HTTPS in production when the API is HTTPS. Do not put secret keys in frontend files; browser code only needs the public API URL and public payment configuration where applicable.

## Backend Configuration

Copy `backend/.env.example` to `backend/.env`. Important settings include:

| Variable | Purpose |
| --- | --- |
| `DEBUG` | Enables development behavior and SQL echoing when true |
| `DATABASE_URL` | Async PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing secret; required and unique in production |
| `CORS_ORIGINS` | Comma-separated browser origins without trailing slashes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `GOOGLE_*` | Google OAuth credentials and callback URL |
| `LINKEDIN_*` | LinkedIn OAuth credentials and callback URL |
| `STRIPE_*` | Stripe server and public keys |
| `RAZORPAY_*` | Razorpay credentials |
| `OPENAI_API_KEY` | Optional AI integration credential |
| `AWS_*` | Optional S3 storage credentials |
| `SENTRY_DSN` | Optional error tracking DSN |

Never commit a real `.env` file, private key, payment secret, OAuth secret, or database password.

## Application Features

### Available application areas

- Email registration and login
- JWT-protected user sessions
- Mentor search and mentor profiles
- Mentor onboarding
- Session booking, cancellation, cost calculation, and feedback
- Communities, membership, posts, and discussion feeds
- Direct messaging
- Notifications and read status
- Payment creation and confirmation flows
- Student, mentor, and admin dashboards
- Profile and account settings

### Feature flags

Optional or roadmap functionality is controlled in `campusconnect-frontend/js/config.js`, including:

- AI mentor matching
- AI career advisor
- Resume analysis
- Google and LinkedIn sign-in UI
- WebSocket chat
- Advanced search
- Admin analytics
- Wallet functionality

Only enable a flag after its backend endpoint, credentials, and frontend flow have been verified.

## API Surface

All application routes use the `/api` prefix.

| Area | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Mentors | `GET /api/mentors/search`, `GET /api/mentors/{id}`, `POST /api/mentors/become-mentor`, `POST /api/mentors/calculate-cost` |
| Bookings | `POST /api/bookings/`, `GET /api/bookings/{id}`, `POST /api/bookings/{id}/cancel`, `POST /api/bookings/{id}/feedback` |
| Communities | `POST /api/communities/`, `GET /api/communities/{id}`, `POST /api/communities/{id}/join`, `POST /api/communities/{id}/posts`, `GET /api/communities/{id}/posts` |
| Messaging | `POST /api/messages/send`, `GET /api/messages/conversation/{id}`, `POST /api/messages/mark-read/{id}` |
| Payments | `POST /api/payments/create`, `POST /api/payments/confirm/{id}` |
| Notifications | `GET /api/notifications/`, `POST /api/notifications/{id}/read` |

The generated OpenAPI document at `/openapi.json` and Swagger UI at `/docs` are the authoritative runtime contract.

Example login request:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

Use the returned access token for protected requests:

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access-token>"
```

## Authentication

1. The frontend submits credentials to `POST /api/auth/login`.
2. The backend returns an access token and, when configured, a refresh token.
3. The frontend stores tokens in browser `localStorage`.
4. `api.js` attaches the access token as a Bearer token to authenticated requests.
5. A rejected or expired session is cleared and redirected to `login.html`.

For higher-security deployments, review the token storage strategy against your threat model before exposing the service publicly. Always use HTTPS and configure secure headers at the hosting layer.

## Database and Migrations

The application uses SQLAlchemy's asynchronous engine with PostgreSQL and AsyncPG.

Create a migration after a model change:

```bash
cd backend
alembic revision --autogenerate -m "Describe schema change"
```

Apply migrations:

```bash
alembic upgrade head
```

For a new development database, the existing initialization utility can create tables:

```bash
python -c "from core.config.database import init_db; import asyncio; asyncio.run(init_db())"
```

Use migrations for shared or production databases. Back up production data before applying schema changes.

## Testing and Validation

Backend syntax validation:

```bash
python -m compileall -q backend
```

Run the Python test suite when tests are present:

```bash
cd backend
pytest
```

Formatting and linting commands:

```bash
black .
pylint modules/
```

 MIT license in the component documentation. Confirm the intended license and add the formal license file before public distribution.
