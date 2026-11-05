# Setup Guide for AI Blog Generation Platform

## Quick Start

### 1. Environment Setup

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_actual_api_key_here
```

### 2. Start Services with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- SearXNG (port 8080)
- FastAPI App (port 8000)

### 3. Run Database Migrations

```bash
docker-compose exec app alembic upgrade head
```

### 4. Verify Installation

Check if services are running:
```bash
docker-compose ps
```

Test the API:
```bash
curl http://localhost:8000/
```

Visit interactive docs: http://localhost:8000/docs

## Starting SearXNG

SearXNG is included in the Docker Compose stack. It starts automatically when you run `docker-compose up -d`.

To start SearXNG only:
```bash
docker-compose up -d searxng
```

Check SearXNG status:
```bash
docker-compose ps searxng
```

Access SearXNG web interface: http://localhost:8080

## Local Development (Without Docker)

If you prefer running the app locally:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start external services:
```bash
docker-compose up -d postgres redis searxng
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the app:
```bash
uvicorn app.main:app --reload
```

## Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Troubleshooting

### Services not starting
```bash
docker-compose logs
```

### Database connection issues
```bash
docker-compose logs postgres
```

### API not accessible
```bash
docker-compose logs app
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```

## Stopping Services

```bash
docker-compose down
```

To stop and remove volumes:
```bash
docker-compose down -v
```
