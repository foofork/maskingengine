#!/usr/bin/env python
"""Run the MaskingEngine REST API server."""

import os
import uvicorn
from api.main import app, API_HOST, API_PORT

if __name__ == "__main__":
    print(f"🚀 Starting MaskingEngine API on http://{API_HOST}:{API_PORT}")
    print(f"📚 API Documentation: http://{API_HOST}:{API_PORT}/docs")
    print(f"🔍 ReDoc Documentation: http://{API_HOST}:{API_PORT}/redoc")
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=os.getenv("API_RELOAD", "true").lower() == "true"
    )