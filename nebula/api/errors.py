"""Error handlers for FastAPI application"""

import uuid
from datetime import datetime
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from nebula.api.schemas import ErrorResponse
from nebula.observability import get_logger

logger = get_logger(__name__)


async def request_validation_error_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handle request validation errors (422)"""
    request_id = str(uuid.uuid4())

    error_details = {
        "errors": exc.errors(),
        "body": getattr(exc, "body", None)
    }

    logger.warning(
        f"Request validation error [{request_id}]: {exc.errors()}"
    )

    error_response = ErrorResponse(
        request_id=request_id,
        error_type="ValidationError",
        message="Request validation failed",
        details=error_details
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions (400)"""
    request_id = str(uuid.uuid4())

    logger.warning(f"ValueError [{request_id}]: {str(exc)}")

    error_response = ErrorResponse(
        request_id=request_id,
        error_type="ValueError",
        message=str(exc),
        details=None
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )


async def file_not_found_error_handler(
    request: Request,
    exc: FileNotFoundError
) -> JSONResponse:
    """Handle FileNotFoundError exceptions (404)"""
    request_id = str(uuid.uuid4())

    logger.warning(f"FileNotFoundError [{request_id}]: {str(exc)}")

    error_response = ErrorResponse(
        request_id=request_id,
        error_type="FileNotFoundError",
        message=str(exc),
        details=None
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions (500)"""
    request_id = str(uuid.uuid4())

    logger.error(
        f"Unhandled exception [{request_id}]: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )

    error_response = ErrorResponse(
        request_id=request_id,
        error_type=type(exc).__name__,
        message="Internal server error",
        details={"error": str(exc)} if logger.level <= 10 else None  # Debug mode only
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with the FastAPI application

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(ValidationError, request_validation_error_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(FileNotFoundError, file_not_found_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Error handlers registered")
