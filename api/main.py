"""MaskingEngine REST API using FastAPI."""

import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from maskingengine import sanitize, rehydrate
from maskingengine.core.config import SanitizerConfig


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
    content: str = Field(..., description="Content to sanitize")
    format: str = Field("text", description="Content format: text, json, or html")
    min_confidence: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    whitelist: Optional[List[str]] = Field(None, description="Terms to exclude from masking")
    placeholder_prefix: str = Field("MASKED_", description="Prefix for masked placeholders")
    enable_ner: bool = Field(True, description="Enable NER-based detection")
    enable_regex: bool = Field(True, description="Enable regex-based detection")


class SanitizeResponse(BaseModel):
    """Response model for sanitize endpoint."""
    sanitized_content: str = Field(..., description="Sanitized content with PII masked")
    mask_map: Dict[str, Any] = Field(..., description="Mapping of placeholders to masked values")
    detection_count: int = Field(..., description="Number of PII entities detected")
    format: str = Field(..., description="Content format used")


class RehydrateRequest(BaseModel):
    """Request model for rehydrate endpoint."""
    sanitized_content: str = Field(..., description="Sanitized content to rehydrate")
    mask_map: Dict[str, Any] = Field(..., description="Mapping of placeholders to original values")
    format: str = Field("text", description="Content format: text, json, or html")


class RehydrateResponse(BaseModel):
    """Response model for rehydrate endpoint."""
    original_content: str = Field(..., description="Original content with PII restored")
    placeholders_restored: int = Field(..., description="Number of placeholders restored")


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    ner_model_loaded: bool = Field(..., description="Whether NER model is loaded")


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint providing API information."""
    return {
        "service": "MaskingEngine API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test if NER model can be loaded
        config = SanitizerConfig(enable_ner=True, enable_regex=False)
        test_result = sanitize("Test", config=config)
        ner_loaded = True
    except Exception:
        ner_loaded = False
    
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        ner_model_loaded=ner_loaded
    )


@app.post("/sanitize", response_model=SanitizeResponse)
async def sanitize_content(request: SanitizeRequest):
    """Sanitize content by masking PII entities."""
    try:
        # Create configuration from request
        config = SanitizerConfig(
            min_confidence=request.min_confidence,
            whitelist=set(request.whitelist) if request.whitelist else None,
            placeholder_prefix=request.placeholder_prefix,
            enable_ner=request.enable_ner,
            enable_regex=request.enable_regex,
        )
        
        # Perform sanitization
        result = sanitize(
            content=request.content,
            format=request.format,
            config=config
        )
        
        return SanitizeResponse(
            sanitized_content=result.sanitized_content,
            mask_map=result.mask_map,
            detection_count=len(result.mask_map),
            format=request.format
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
    """Rehydrate sanitized content by restoring masked values."""
    try:
        # Perform rehydration
        original_content = rehydrate(
            sanitized_content=request.sanitized_content,
            mask_map=request.mask_map,
            format=request.format
        )
        
        return RehydrateResponse(
            original_content=original_content,
            placeholders_restored=len(request.mask_map)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)