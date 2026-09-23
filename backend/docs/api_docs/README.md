# CampusConnect Backend Documentation

## Project Structure

'''
backend/
├── app/                    # Application package
├── core/                   # Core configurations and utilities
│   ├── config/             # Settings, database, security
│   ├── middleware/         # FastAPI middleware
│   ├── dependencies/       # FastAPI dependencies
│   ├── events/             # Event bus
│   └── exceptions/         # Custom exceptions
├── modules/                # Feature modules
│   ├── auth/               # Authentication
│   ├── users/              # User management
│   ├── mentorship/         # Mentor marketplace
│   ├── bookings/           # Session bookings
│   ├── communities/        # Community platform
│   ├── messaging/          # Direct messaging
│   ├── payments/           # Payment processing
│   ├── notifications/      # Notifications
│   ├── profiles/           # User profiles
│   ├── ai/                 # AI services
│   ├── admin/              # Admin panel
│   ├── verification/       # Mentor verification
│   └── discussions/        # Discussions
├── integrations/           # Third-party integrations
│   ├── google/             # Google OAuth
│   ├── linkedin/           # LinkedIn OAuth
│   ├── stripe/             # Stripe payments
│   └── razorpay/           # Razorpay payments
├── storage/                # File storage
│   └── s3/                 # AWS S3
├── websocket/              # WebSocket functionality
├── database/               # Database utilities
├── monitoring/             # Monitoring and metrics
├── main.py                 # FastAPI application entry point
├── pyproject.toml          # Project configuration
├── requirements.txt        # Dependencies
└── .env.example            # Environment variables template
''''

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis 6+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment file:
```bash
cp .env.example .env
```

5. Update `.env` with your configuration:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/campusconnect

# Add other required configurations
```

6. Initialize database:
```bash
# Run migrations (if using Alembic)
alembic upgrade head
```

### Running the Application

```bash
python main.py
```

Or using Uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user profile

### Mentorship
- `POST /api/mentors/become-mentor` - Become a mentor
- `GET /api/mentors/search` - Search mentors
- `GET /api/mentors/{mentor_id}` - Get mentor profile
- `POST /api/mentors/calculate-cost` - Calculate session cost

### Bookings
- `POST /api/bookings` - Create booking
- `GET /api/bookings/{session_id}` - Get booking details
- `POST /api/bookings/{session_id}/cancel` - Cancel booking
- `POST /api/bookings/{session_id}/feedback` - Add feedback

### Communities
- `POST /api/communities` - Create community
- `GET /api/communities/{community_id}` - Get community
- `POST /api/communities/{community_id}/join` - Join community
- `POST /api/communities/{community_id}/posts` - Create post
- `GET /api/communities/{community_id}/posts` - Get posts

### Messaging
- `POST /api/messages/send` - Send message
- `GET /api/messages/conversation/{user_id}` - Get conversation
- `POST /api/messages/mark-read/{message_id}` - Mark as read

### Payments
- `POST /api/payments/create` - Create payment
- `POST /api/payments/confirm/{payment_id}` - Confirm payment

## Technology Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Cache**: Redis
- **Authentication**: JWT
- **Payments**: Stripe, Razorpay
- **AI**: OpenAI GPT-4
- **Storage**: AWS S3

### Development
- **Testing**: pytest
- **Linting**: pylint, black
- **Monitoring**: Prometheus, Sentry

## Configuration

### Environment Variables
See `.env.example` for all available configuration options.

### Database Models
- **User**: User accounts and profiles
- **Session**: Mentorship sessions
- **Community**: Community groups
- **Post**: Community posts
- **Message**: Direct messages
- **Payment**: Payment records
- **Notification**: User notifications

## Features

### MVP Features
- ✅ User authentication (Email, Google, LinkedIn)
- ✅ User profiles
- ✅ Mentor marketplace
- ✅ Session booking system
- ✅ Payment processing
- ✅ Community platform
- ✅ Direct messaging
- ✅ Notifications

### AI Features
- ✅ Mentor matching
- ✅ Resume analysis
- ✅ Career advisor
- ✅ Semantic search
- ✅ Content moderation

### Business Rules
- Same college professor mentorship: Free
- Same college senior mentorship: Free
- Same college alumni: 45% discount
- External mentors: Standard pricing
- Platform commission: 10-20% (configurable)

## Deployment

### Docker
```bash
docker-compose up -d
```

### Production
1. Set `DEBUG=False` in environment
2. Update `SECRET_KEY` with strong value
3. Configure proper database backups
4. Set up monitoring and logging
5. Enable HTTPS

## Testing

```bash
pytest
```

## Contributing

1. Create feature branch: `git checkout -b feature/feature-name`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/feature-name`
4. Open pull request

## License

MIT License
