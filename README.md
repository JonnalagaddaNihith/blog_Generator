# AI Blog Generation Platform - Backend

A powerful backend system for generating AI-powered company blogs using FastAPI, PostgreSQL, LangGraph, and external AI services.

## Features

- **9 Specialized AI Agents**: Web Research, Keyword Intelligence, Competitor Gap Analysis, Blog Strategy, Blog Writing, SEO, Image Generation, Quality Assurance, and Fact Verification
- **LangGraph Workflow**: Interrupt-based human approval system for outline and final blog review
- **External API Integrations**:
  - SearXNG (self-hosted web search)
  - OpenRouter (text and image generation)
- **PostgreSQL Database**: Full persistence for projects, research, keywords, outlines, blog versions, and reports
- **Redis Caching**: Performance optimization for API responses
- **PDF Export**: Generate professional PDFs from approved blogs
- **REST API**: Complete CRUD operations for all entities
- **Docker Support**: Easy deployment with Docker Compose

## Architecture

### Tech Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI Orchestration**: LangGraph
- **Caching**: Redis
- **Search**: SearXNG (local Docker instance)
- **AI Services**: OpenRouter (DeepSeek for text, Qwen for images)
- **PDF Generation**: ReportLab
- **Testing**: pytest with pytest-asyncio
- **Migrations**: Alembic

### Project Structure

```
blog_generator/
├── app/
│   ├── api/v1/          # REST API endpoints
│   ├── agents/          # AI agents for blog generation
│   ├── models/          # SQLAlchemy database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # External service integrations
│   ├── storage/         # File management
│   └── utils/           # Utilities (logger, validators)
├── alembic/             # Database migrations
├── storage/             # Local storage for images and PDFs
├── tests/               # Test suite
├── docker-compose.yml   # Docker orchestration
├── Dockerfile           # Application container
└── requirements.txt     # Python dependencies
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenRouter API key

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd blog_generator
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - SearXNG (port 8080)
   - FastAPI application (port 8000)

4. **Run database migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Verify the API**
   ```bash
   curl http://localhost:8000/
   ```

   Visit `http://localhost:8000/docs` for interactive API documentation.

### Local Development Setup

1. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration.

4. **Start external services**
   ```bash
   docker-compose up -d postgres redis searxng
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://...` |
| `DATABASE_SYNC_URL` | PostgreSQL sync connection string (for Alembic) | `postgresql://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SEARXNG_URL` | SearXNG instance URL | `http://localhost:8080` |
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `OPENROUTER_TEXT_MODEL` | Text generation model | `deepseek/deepseek-v4-pro-0813` |
| `OPENROUTER_IMAGE_MODEL` | Image generation model | `qwen/qwen-image-2.1-turbo` |
| `STORAGE_IMAGES_PATH` | Path to store generated images | `./storage/images` |
| `STORAGE_PDFS_PATH` | Path to store generated PDFs | `./storage/pdfs` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `APP_HOST` | Application host | `0.0.0.0` |
| `APP_PORT` | Application port | `8000` |

## API Documentation

### Companies API

- `POST /api/v1/companies/` - Create a company
- `GET /api/v1/companies/` - List all companies
- `GET /api/v1/companies/{id}` - Get a company
- `PUT /api/v1/companies/{id}` - Update a company
- `DELETE /api/v1/companies/{id}` - Delete a company

### Projects API

- `POST /api/v1/projects/` - Create a project
- `GET /api/v1/projects/` - List all projects
- `GET /api/v1/projects/{id}` - Get a project
- `PUT /api/v1/projects/{id}` - Update a project
- `DELETE /api/v1/projects/{id}` - Delete a project

### Research API

- `GET /api/v1/projects/{project_id}/research` - Get research data
- `POST /api/v1/projects/{project_id}/research` - Trigger research

### Outlines API

- `GET /api/v1/projects/{project_id}/outlines` - List outlines
- `GET /api/v1/outlines/{id}` - Get an outline
- `PUT /api/v1/outlines/{id}` - Update outline (for editing)
- `POST /api/v1/outlines/{id}/approve` - Approve outline
- `POST /api/v1/outlines/{id}/reject` - Reject outline

### Blogs API

- `GET /api/v1/projects/{project_id}/blogs` - List blog versions
- `GET /api/v1/blogs/{id}` - Get a blog version
- `PUT /api/v1/blogs/{id}` - Update blog version
- `POST /api/v1/blogs/{id}/approve` - Approve final blog
- `POST /api/v1/blogs/{id}/reject` - Reject final blog

### Workflow API

- `POST /api/v1/projects/{project_id}/workflow/start` - Start generation workflow
- `POST /api/v1/projects/{project_id}/workflow/resume` - Resume after interrupt
- `GET /api/v1/projects/{project_id}/workflow/status` - Get workflow status

### Export API

- `POST /api/v1/blogs/{id}/export/pdf` - Export approved blog as PDF
- `GET /api/v1/blogs/{id}/export/pdf/{filename}` - Download generated PDF

## Workflow Explanation

The blog generation workflow uses LangGraph with interrupt-based human approval:

### Stage 1: Research and Outline

1. **Web Research Agent**: Searches for 10-15 relevant results using SearXNG
2. **Keyword Intelligence Agent**: Extracts primary, secondary, and long-tail keywords
3. **Competitor Gap Agent**: Analyzes competitor content and identifies gaps
4. **Blog Strategy Agent**: Generates differentiated strategy and structured outline
5. **Interrupt**: Workflow pauses for human outline approval

### Stage 2: Content Generation

After outline approval:
6. **Blog Writing Agent**: Writes the complete blog content
7. **SEO Agent**: Optimizes title, metadata, keywords, and headings
8. **Image Agent**: Generates a featured image
9. **Quality Agent**: Validates grammar and readability
10. **Fact Verification Agent**: Verifies factual claims
11. **Interrupt**: Workflow pauses for final human approval

### Resume Mechanism

- **Stage 1 Resume**: Edit outline via `PUT /api/v1/outlines/{id}`, then call `POST /api/v1/projects/{project_id}/workflow/resume`
- **Stage 2 Resume**: After final review, approve or reject the blog

### Version Management

- Every revision creates a new version
- Editing approved content invalidates approval
- PDF export requires final approval

## Testing

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_api/test_companies.py
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Test coverage includes:
- Unit tests for services (SearXNG, OpenRouter, PDF generator)
- Integration tests for API endpoints
- Database model tests
- Workflow state transition tests

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migrations
```bash
alembic downgrade -1
```

## Troubleshooting

### SearXNG not accessible
- Ensure SearXNG container is running: `docker-compose ps searxng`
- Check logs: `docker-compose logs searxng`
- Verify port 8080 is not in use

### Database connection errors
- Check PostgreSQL container: `docker-compose ps postgres`
- Verify DATABASE_URL in .env
- Ensure migrations are applied: `alembic upgrade head`

### Redis connection errors
- Check Redis container: `docker-compose ps redis`
- Verify REDIS_URL in .env
- Redis is optional; the app will work without it (just slower)

### OpenRouter API errors
- Verify OPENROUTER_API_KEY is set correctly
- Check your OpenRouter account credits
- Review API rate limits

### LangGraph workflow stuck
- Check PostgreSQL checkpoint table for state
- Verify database connection is stable
- Review workflow status via API endpoint

## Security Notes

- **Never commit API keys** to the repository
- Use environment variables for all sensitive data
- Enable authentication in production (not implemented in Phase 1)
- Use HTTPS in production
- Implement rate limiting for API endpoints
- Regularly update dependencies

## Future Enhancements

- User authentication and authorization
- Frontend web application
- Advanced workflow customization
- Support for additional AI models
- Real-time workflow monitoring
- Analytics and reporting dashboard
- Multi-language support
- Template management

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.
