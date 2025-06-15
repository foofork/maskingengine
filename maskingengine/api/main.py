"""MaskingEngine REST API using FastAPI."""

import os
from typing import Optional, Dict, Any, List, Union
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from maskingengine import Sanitizer, Config, Rehydrator, RehydrationPipeline, RehydrationStorage


# Get configuration from environment or use defaults
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_TITLE = os.getenv("API_TITLE", "MaskingEngine API")
API_DESCRIPTION = os.getenv("API_DESCRIPTION", "Local-first PII sanitization service")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SanitizeRequest(BaseModel):
    """Request model for sanitize endpoint."""
    content: Union[str, Dict[str, Any]] = Field(..., description="Content to sanitize")
    format: Optional[str] = Field(None, description="Content format: text, json, or html (auto-detect if not specified)")
    regex_only: bool = Field(False, description="Use regex-only mode (faster)")
    pattern_packs: Optional[List[str]] = Field(None, description="Pattern packs to use (defaults to ['default'])")
    whitelist: Optional[List[str]] = Field(None, description="Terms to exclude from masking")
    min_confidence: Optional[float] = Field(None, description="Minimum confidence threshold for NER")
    strict_validation: bool = Field(True, description="Enable strict validation (e.g., Luhn check for credit cards)")


class SanitizeResponse(BaseModel):
    """Response model for sanitize endpoint."""
    sanitized_content: Union[str, Dict[str, Any]] = Field(..., description="Sanitized content with PII masked")
    mask_map: Dict[str, str] = Field(..., description="Mapping of placeholders to masked values")
    detection_count: int = Field(..., description="Number of PII entities detected")


class RehydrateRequest(BaseModel):
    """Request model for rehydrate endpoint."""
    masked_content: Union[str, Dict[str, Any]] = Field(..., description="Content with PII placeholders")
    mask_map: Dict[str, str] = Field(..., description="Mapping of placeholders to original values")


class RehydrateResponse(BaseModel):
    """Response model for rehydrate endpoint."""
    rehydrated_content: Union[str, Dict[str, Any]] = Field(..., description="Content with original PII restored")
    placeholders_found: int = Field(..., description="Number of placeholders processed")


class SessionSanitizeRequest(BaseModel):
    """Request model for session-based sanitize endpoint."""
    content: Union[str, Dict[str, Any]] = Field(..., description="Content to sanitize")
    session_id: str = Field(..., description="Unique session identifier")
    format: Optional[str] = Field(None, description="Content format: text, json, or html")
    regex_only: bool = Field(False, description="Use regex-only mode (faster)")
    pattern_packs: Optional[List[str]] = Field(None, description="Pattern packs to use")
    whitelist: Optional[List[str]] = Field(None, description="Terms to exclude from masking")
    min_confidence: Optional[float] = Field(None, description="Minimum confidence threshold for NER")
    strict_validation: bool = Field(True, description="Enable strict validation")


class SessionSanitizeResponse(BaseModel):
    """Response model for session-based sanitize endpoint."""
    sanitized_content: Union[str, Dict[str, Any]] = Field(..., description="Sanitized content with PII masked")
    session_id: str = Field(..., description="Session identifier for rehydration")
    storage_path: str = Field(..., description="Path where mask map is stored")
    detection_count: int = Field(..., description="Number of PII entities detected")


class SessionRehydrateRequest(BaseModel):
    """Request model for session-based rehydrate endpoint."""
    masked_content: Union[str, Dict[str, Any]] = Field(..., description="Content with PII placeholders")
    session_id: str = Field(..., description="Session identifier")


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    ner_enabled: bool = Field(..., description="Whether NER detection is enabled")


# Initialize rehydration system
rehydration_storage = RehydrationStorage()
rehydration_pipeline = None  # Will be initialized with first sanitizer


def get_rehydration_pipeline():
    """Get or create rehydration pipeline."""
    global rehydration_pipeline
    if rehydration_pipeline is None:
        sanitizer = Sanitizer()
        rehydration_pipeline = RehydrationPipeline(sanitizer, rehydration_storage)
    return rehydration_pipeline


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint providing API information."""
    return {
        "service": "MaskingEngine API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "sanitize": "/sanitize",
            "rehydrate": "/rehydrate", 
            "session_sanitize": "/session/sanitize",
            "session_rehydrate": "/session/rehydrate"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test basic functionality
        sanitizer = Sanitizer()
        test_content, test_map = sanitizer.sanitize("test@example.com")
        
        return HealthResponse(
            status="healthy",
            version=API_VERSION,
            ner_enabled=sanitizer.config.NER_ENABLED
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@app.post("/sanitize", response_model=SanitizeResponse)
async def sanitize_content(request: SanitizeRequest):
    """Sanitize content by masking PII entities."""
    try:
        # Create configuration from request
        config = Config(
            pattern_packs=request.pattern_packs or ["default"],
            whitelist=request.whitelist or [],
            min_confidence=request.min_confidence,
            strict_validation=request.strict_validation,
            regex_only=request.regex_only
        )
        
        # Create sanitizer
        sanitizer = Sanitizer(config)
        
        # Perform sanitization
        sanitized_content, mask_map = sanitizer.sanitize(
            request.content,
            format=request.format
        )
        
        return SanitizeResponse(
            sanitized_content=sanitized_content,
            mask_map=mask_map,
            detection_count=len(mask_map)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.post("/rehydrate", response_model=RehydrateResponse)
async def rehydrate_content(request: RehydrateRequest):
    """Rehydrate masked content using provided mask map."""
    try:
        rehydrator = Rehydrator()
        
        # Validate mask map
        is_valid, issues = rehydrator.validate_mask_map(request.mask_map)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mask map: {'; '.join(issues)}"
            )
        
        # Check rehydration compatibility  
        can_rehydrate, compatibility_issues = rehydrator.check_rehydration_compatibility(
            request.masked_content, request.mask_map
        )
        if not can_rehydrate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rehydration compatibility issues: {'; '.join(compatibility_issues)}"
            )
        
        # Perform rehydration
        rehydrated_content = rehydrator.rehydrate(request.masked_content, request.mask_map)
        placeholders_found = len(rehydrator.extract_placeholders(request.masked_content))
        
        return RehydrateResponse(
            rehydrated_content=rehydrated_content,
            placeholders_found=placeholders_found
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.post("/session/sanitize", response_model=SessionSanitizeResponse)
async def session_sanitize(request: SessionSanitizeRequest):
    """Sanitize content and store mask map for later rehydration."""
    try:
        # Create configuration from request
        config = Config(
            pattern_packs=request.pattern_packs or ["default"],
            whitelist=request.whitelist or [],
            min_confidence=request.min_confidence,
            strict_validation=request.strict_validation,
            regex_only=request.regex_only
        )
        
        # Get rehydration pipeline
        pipeline = get_rehydration_pipeline()
        pipeline.sanitizer = Sanitizer(config)  # Update with new config
        
        # Perform sanitization with session storage
        sanitized_content, storage_path = pipeline.sanitize_with_session(
            request.content,
            request.session_id,
            request.format
        )
        
        # Count detections by loading the stored mask map
        mask_map = pipeline.storage.load_mask_map(request.session_id)
        detection_count = len(mask_map) if mask_map else 0
        
        return SessionSanitizeResponse(
            sanitized_content=sanitized_content,
            session_id=request.session_id,
            storage_path=storage_path,
            detection_count=detection_count
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.post("/session/rehydrate", response_model=RehydrateResponse)
async def session_rehydrate(request: SessionRehydrateRequest):
    """Rehydrate content using stored session mask map."""
    try:
        pipeline = get_rehydration_pipeline()
        
        # Attempt rehydration with session
        rehydrated_content = pipeline.rehydrate_with_session(
            request.masked_content,
            request.session_id
        )
        
        if rehydrated_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{request.session_id}' not found or expired"
            )
        
        # Count placeholders that were processed
        rehydrator = Rehydrator()
        placeholders_found = len(rehydrator.extract_placeholders(request.masked_content))
        
        return RehydrateResponse(
            rehydrated_content=rehydrated_content,
            placeholders_found=placeholders_found
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete stored session and cleanup mask map."""
    try:
        pipeline = get_rehydration_pipeline()
        success = pipeline.complete_session(session_id)
        
        if success:
            return {"message": f"Session '{session_id}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    try:
        pipeline = get_rehydration_pipeline()
        sessions = pipeline.storage.list_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)