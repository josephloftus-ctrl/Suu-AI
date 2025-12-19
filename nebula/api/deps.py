"""Dependency injection for FastAPI application"""

from typing import Optional
from fastapi import HTTPException, status

from nebula.engine import NebulaEngine
from nebula.observability import get_logger

logger = get_logger(__name__)

# Global engine instance
_engine: Optional[NebulaEngine] = None


def set_engine(engine: NebulaEngine) -> None:
    """
    Set the global engine instance

    Args:
        engine: NebulaEngine instance to set
    """
    global _engine
    _engine = engine
    logger.info("Engine set in dependencies")


def clear_engine() -> None:
    """Clear the global engine instance"""
    global _engine
    _engine = None
    logger.info("Engine cleared from dependencies")


def get_engine() -> NebulaEngine:
    """
    Get the global engine instance

    Returns:
        NebulaEngine instance

    Raises:
        HTTPException: 503 if engine is not initialized
    """
    if _engine is None:
        logger.error("Engine not initialized - service unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Engine not initialized"
        )
    return _engine
