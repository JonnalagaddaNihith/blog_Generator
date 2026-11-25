from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import companies, projects, workflow, export, sql_websites
from app.utils.logger import logger
from app.cache import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting AI Blog Generation Platform API")
    yield
    # Shutdown
    logger.info("Shutting down AI Blog Generation Platform API")
    await close_redis()


app = FastAPI(
    title="AI Blog Generation Platform",
    description="Backend API for AI-powered company blog generation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(workflow.router, prefix="/api/v1", tags=["workflow"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])
app.include_router(sql_websites.router, prefix="/api/v1", tags=["sql-websites"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Blog Generation Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
