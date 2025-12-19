"""API schemas and Pydantic models for Nebula Engine"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Artifact(BaseModel):
    """File artifact returned from processing"""
    name: str = Field(..., description="Artifact filename")
    path: str = Field(..., description="Path to artifact")
    size_bytes: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the artifact")


class ErrorResponse(BaseModel):
    """Standard error response"""
    request_id: str = Field(..., description="Unique request identifier")
    status: Literal["error"] = "error"
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class JobResponse(BaseModel):
    """Standard job response"""
    request_id: str = Field(..., description="Unique request identifier")
    status: Literal["ok", "warning", "error"] = Field(..., description="Job status")
    started_at: datetime = Field(..., description="Job start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Job finish timestamp")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    artifacts: Optional[List[Artifact]] = Field(None, description="Generated artifacts")
    warnings: Optional[List[str]] = Field(None, description="Warning messages")
    errors: Optional[List[str]] = Field(None, description="Error messages")


class AssignLocationRequest(BaseModel):
    """Request to assign location for an item"""
    description: str = Field(..., description="Item description", min_length=1)
    category: Optional[str] = Field(None, description="Item category")


class AssignLocationResponse(BaseModel):
    """Response with assigned location"""
    location: Optional[str] = Field(None, description="Assigned location code")
    matched_by: Optional[str] = Field(None, description="How location was assigned (category/keyword)")
    description: str = Field(..., description="Item description")
    category: Optional[str] = Field(None, description="Item category")


class SortQueryParams(BaseModel):
    """Query parameters for sort operation"""
    location_code: str = Field(..., description="Location code (e.g., KG001)")
    mode: Literal["production", "development"] = Field("production", description="Processing mode")
    dry_run: bool = Field(False, description="If true, validate only without processing")


class HealthResponse(BaseModel):
    """Health check response"""
    version: str = Field(..., description="API version")
    status: str = Field(..., description="Overall health status")
    engine: Dict[str, Any] = Field(..., description="Engine health details")
    rules_count: int = Field(..., description="Number of inventory rules loaded")
