# Production Dockerfile for MaskingEngine (with NER support)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal requirements first for faster builds
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy the application code
COPY maskingengine/ ./maskingengine/
COPY setup.py .
COPY README.md .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 maskinguser && chown -R maskinguser:maskinguser /app
USER maskinguser

# Create model cache directory
RUN mkdir -p /home/maskinguser/.cache/huggingface

# Expose API port
EXPOSE 8000

# Default command runs the API server
# NER models will be downloaded on first use
CMD ["uvicorn", "maskingengine.api.main:app", "--host", "0.0.0.0", "--port", "8000"]