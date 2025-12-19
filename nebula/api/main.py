"""FastAPI application entry point for Nebula Engine"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from nebula.engine import NebulaEngine
from nebula.api import __version__
from nebula.api.deps import set_engine, clear_engine
from nebula.api.errors import register_error_handlers
from nebula.api.routes import health, inventory, templog
from nebula.observability import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application
    Initializes and cleans up resources
    """
    # Startup
    logger.info("Starting Nebula Engine API")
    configure_logging(level="INFO")

    # Initialize engine once at startup
    engine = NebulaEngine()
    set_engine(engine)
    logger.info("Engine initialized and set")

    yield

    # Shutdown
    logger.info("Shutting down Nebula Engine API")
    clear_engine()


# Create FastAPI application
app = FastAPI(
    title="Nebula Engine API",
    description="AI-Powered Kitchen Operating System API",
    version=__version__,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(inventory.router, prefix="/api/v1", tags=["inventory"])
app.include_router(templog.router, prefix="/api/v1", tags=["templog"])


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
