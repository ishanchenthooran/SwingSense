# SwingSense Backend
.\.venv\Scripts\Activate
uvicorn app.main:app --reload --port 8000

npm run dev

A FastAPI backend for the SwingSense golf application.

## Features

- FastAPI with Uvicorn server
- SQLAlchemy (sync) with Alembic migrations
- PostgreSQL database (Supabase)
- Supabase Auth JWT token parsing
- OpenAI Chat completions integration
- CORS support for frontend development
- Environment-based configuration

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database (or Supabase)
- OpenAI API key

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd swingsense-backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment template and configure:
```bash
cp .env.example .env
```

Edit `.env` with your actual configuration values:
- `DATABASE_URL`: Your PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `SUPABASE_JWKS_URL`: Your Supabase JWKS URL
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

### Database Setup

1. Create the database (if using local PostgreSQL):
```bash
createdb swingsense
```

2. Run migrations:
```bash
alembic upgrade head
```

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /healthz` - Returns `{"status": "ok"}`

### User Management
- `GET /me` - Get current user profile
- `PUT /me` - Update user profile

### Questions & Feedback
- `POST /questions` - Ask a question (OpenAI integration)
- `GET /questions/feedback` - Get latest feedback

### Training Plans
- `POST /plans/generate` - Generate a training plan
- `GET /plans/current` - Get current training plan

### Progress Tracking
- `POST /progress` - Record progress metrics
- `GET /progress` - Get progress data (with optional date range)

### Resources
- `GET /resources` - Get resources (optionally filtered by issue tag)

## Testing with curl

### Health Check
```bash
curl http://localhost:8000/healthz
```

### Authenticated Endpoints
For endpoints requiring authentication, include the JWT token in the Authorization header:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/me
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/questions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How can I improve my golf swing?"}'
```

### Generate a Training Plan
```bash
curl -X POST http://localhost:8000/plans/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"goals": ["improve accuracy", "increase distance"], "skill_level": "intermediate"}'
```

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

### Project Structure

```
app/
├── main.py              # FastAPI app factory
├── core/
│   ├── config.py        # Environment configuration
│   └── auth.py          # JWT authentication
├── db/
│   └── session.py       # Database session management
└── routers/
    ├── health.py        # Health check endpoint
    ├── me.py           # User profile management
    ├── questions.py    # Questions and feedback
    ├── plans.py        # Training plans
    ├── progress.py     # Progress tracking
    └── resources.py    # Resource management
```

## Security Notes

- JWT tokens are currently decoded without verification for MVP
- TODO: Implement JWKS verification for production security
- Ensure proper CORS configuration for production
- Use environment variables for all sensitive configuration

## License


