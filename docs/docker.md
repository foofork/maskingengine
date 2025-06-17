# Docker Deployment Guide

This guide covers Docker deployment options for MaskingEngine, including production deployment, development setup, and container orchestration.

## Table of Contents
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
- [Development Setup](#development-setup)
- [Docker Compose](#docker-compose)
- [Container Configuration](#container-configuration)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Running with Docker
```bash
# Pull and run the latest image
docker pull maskingengine:latest
docker run -p 8000:8000 maskingengine:latest

# Or build and run locally
docker build -t maskingengine:latest .
docker run -p 8000:8000 maskingengine:latest
```

### Using Docker Compose
```bash
# Start production service
docker-compose up maskingengine

# Start development service with hot reload
docker-compose up maskingengine-dev
```

## Production Deployment

### Building the Production Image
The production Dockerfile uses a minimal Python 3.9 slim base image for optimal size and security:

```bash
# Build production image
docker build -t maskingengine:latest .

# Tag for registry
docker tag maskingengine:latest your-registry/maskingengine:latest
docker push your-registry/maskingengine:latest
```

### Running in Production
```bash
# Basic production run
docker run -d \
  --name maskingengine-prod \
  -p 8000:8000 \
  --restart unless-stopped \
  maskingengine:latest

# With custom configuration
docker run -d \
  --name maskingengine-prod \
  -p 8000:8000 \
  -v /path/to/configs:/app/configs:ro \
  -v /path/to/pattern_packs:/app/pattern_packs:ro \
  --restart unless-stopped \
  maskingengine:latest

# With environment variables
docker run -d \
  --name maskingengine-prod \
  -p 8000:8000 \
  -e MASKINGENGINE_LOG_LEVEL=INFO \
  -e MASKINGENGINE_WORKERS=4 \
  --restart unless-stopped \
  maskingengine:latest
```

### Health Checks
The production container includes built-in health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' maskingengine-prod

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' maskingengine-prod
```

## Development Setup

### Building the Development Image
The development Dockerfile includes additional tools for development:

```bash
# Build development image
docker build -f Dockerfile.dev -t maskingengine:dev .
```

### Development Features
- Full Python development environment
- Node.js for claude-flow support
- Development tools (vim, git, curl)
- Pre-installed testing and linting tools
- Volume-friendly configuration

### Running Development Container
```bash
# Interactive development shell
docker run -it --rm \
  -v $(pwd):/app \
  -p 8001:8000 \
  maskingengine:dev bash

# Run with hot reload
docker run -it --rm \
  -v $(pwd):/app \
  -p 8001:8000 \
  maskingengine:dev \
  uvicorn maskingengine.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
docker run -it --rm \
  -v $(pwd):/app \
  maskingengine:dev \
  pytest -v --cov=maskingengine

# Run linting
docker run -it --rm \
  -v $(pwd):/app \
  maskingengine:dev \
  bash -c "black --check . && flake8 . && mypy maskingengine"
```

## Docker Compose

### Services Overview
The `docker-compose.yml` file provides multiple services:

1. **maskingengine** - Production service
2. **maskingengine-dev** - Development service with hot reload
3. **test** - Test runner (profile: test)
4. **lint** - Linting and type checking (profile: lint)

### Common Commands
```bash
# Start all default services
docker-compose up

# Start specific service
docker-compose up maskingengine-dev

# Run tests
docker-compose --profile test up

# Run linting
docker-compose --profile lint up

# View logs
docker-compose logs -f maskingengine-dev

# Stop all services
docker-compose down

# Clean up volumes
docker-compose down -v
```

### Custom Configuration
Create a `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  maskingengine-dev:
    environment:
      - CUSTOM_VAR=value
    ports:
      - "8003:8000"
```

## Container Configuration

### Volume Mounts
```bash
# Configuration files (read-only)
-v /path/to/configs:/app/configs:ro

# Pattern packs (read-only)
-v /path/to/pattern_packs:/app/pattern_packs:ro

# Development source code
-v $(pwd):/app:cached
```

### Environment Variables
```bash
# API Configuration
MASKINGENGINE_HOST=0.0.0.0
MASKINGENGINE_PORT=8000
MASKINGENGINE_WORKERS=4
MASKINGENGINE_LOG_LEVEL=INFO

# Python Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Resource Limits
```yaml
# docker-compose.yml example
services:
  maskingengine:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Security Considerations

### Non-Root User
Both production and development images run as a non-root user (UID 1000):

```dockerfile
RUN useradd -m -u 1000 maskinguser
USER maskinguser
```

### Read-Only Volumes
Mount configuration and pattern packs as read-only:

```bash
-v /configs:/app/configs:ro
-v /pattern_packs:/app/pattern_packs:ro
```

### Network Security
```bash
# Limit to localhost only
docker run -p 127.0.0.1:8000:8000 maskingengine:latest

# Use Docker networks for service isolation
docker network create maskingengine-net
docker run --network maskingengine-net maskingengine:latest
```

### Secrets Management
Never hardcode secrets in images. Use environment variables or secrets management:

```bash
# Using Docker secrets (Swarm mode)
echo "secret_value" | docker secret create api_key -
docker service create --secret api_key maskingengine:latest

# Using environment file
docker run --env-file .env maskingengine:latest
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker logs maskingengine-prod

# Check with verbose output
docker run --rm -it maskingengine:latest bash
```

#### Permission Issues
```bash
# Fix volume permissions
docker run --rm -v $(pwd):/app maskingengine:dev \
  chown -R 1000:1000 /app
```

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Use different port
docker run -p 8001:8000 maskingengine:latest
```

#### Memory Issues
```bash
# Check container resources
docker stats maskingengine-prod

# Increase memory limit
docker run -m 4g maskingengine:latest
```

### Debugging

#### Interactive Shell
```bash
# Production image
docker run -it --rm --entrypoint bash maskingengine:latest

# Development image
docker run -it --rm maskingengine:dev bash
```

#### Container Inspection
```bash
# Inspect running container
docker inspect maskingengine-prod

# Check processes
docker top maskingengine-prod

# Export container filesystem
docker export maskingengine-prod > container.tar
```

### Performance Optimization

#### Multi-Stage Build Benefits
- Smaller final image size
- No build dependencies in production
- Faster deployment and scaling

#### Layer Caching
```bash
# Build with cache
docker build -t maskingengine:latest .

# Build without cache
docker build --no-cache -t maskingengine:latest .
```

#### Image Size Optimization
```bash
# Check image size
docker images maskingengine

# Remove unused images
docker image prune -a
```

## Advanced Deployment

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maskingengine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maskingengine
  template:
    metadata:
      labels:
        app: maskingengine
    spec:
      containers:
      - name: maskingengine
        image: maskingengine:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy service
docker service create \
  --name maskingengine \
  --replicas 3 \
  --publish 8000:8000 \
  --limit-cpu 2 \
  --limit-memory 4g \
  maskingengine:latest
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Build and push Docker image
  run: |
    docker build -t maskingengine:${{ github.sha }} .
    docker tag maskingengine:${{ github.sha }} maskingengine:latest
    docker push maskingengine:${{ github.sha }}
    docker push maskingengine:latest
```

## Next Steps

- Review [Security Best Practices](security.md) for production deployments
- See [API Documentation](api.md) for endpoint configuration
- Check [Architecture Overview](architecture.md) for scaling considerations
- Explore [Examples](examples.md) for integration patterns