# MaskingEngine REST API Reference

The MaskingEngine REST API provides a comprehensive HTTP interface for PII detection, masking, and rehydration operations. The API is built with FastAPI and includes automatic OpenAPI documentation.

## Quick Start

```bash
# Start the API server
python run_api.py

# API will be available at:
# - Main API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs  
# - ReDoc docs: http://localhost:8000/redoc
```

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production deployments, consider adding authentication middleware.

## Content Types

The API accepts and returns `application/json` content type for all endpoints.

## Core Endpoints

### Health Check

#### `GET /health`

Check API health and configuration status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0", 
  "ner_enabled": true
}
```

**Response Fields:**
- `status` (string): Health status - "healthy" or "unhealthy"
- `version` (string): API version
- `ner_enabled` (boolean): Whether NER detection is enabled

---

### Root Information

#### `GET /`

Get API information and available endpoints.

**Response:**
```json
{
  "service": "MaskingEngine API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "sanitize": "/sanitize",
    "rehydrate": "/rehydrate",
    "session_sanitize": "/session/sanitize", 
    "session_rehydrate": "/session/rehydrate"
  }
}
```

---

## Sanitization Endpoints

### Basic Sanitization

#### `POST /sanitize`

Sanitize content by masking PII entities and return both sanitized content and mask map.

**Request Body:**
```json
{
  "content": "Contact John at john@example.com or 555-123-4567",
  "format": "text",
  "regex_only": false,
  "pattern_packs": ["default"],
  "whitelist": ["support@company.com"],
  "min_confidence": 0.9,
  "strict_validation": true
}
```

**Request Fields:**
- `content` (string|object, required): Content to sanitize (text, JSON object, or HTML)
- `format` (string, optional): Content format - "text", "json", or "html" (auto-detected if not specified)
- `regex_only` (boolean, optional): Use regex-only mode for faster processing (default: false)
- `pattern_packs` (array, optional): Pattern packs to use (default: ["default"])
- `whitelist` (array, optional): Terms to exclude from masking
- `min_confidence` (number, optional): Minimum confidence threshold for NER detection
- `strict_validation` (boolean, optional): Enable strict validation like Luhn check for credit cards (default: true)

**Response:**
```json
{
  "sanitized_content": "Contact John at <<EMAIL_7A9B2C_1>> or <<PHONE_4D8E1F_1>>",
  "mask_map": {
    "<<EMAIL_7A9B2C_1>>": "john@example.com",
    "<<PHONE_4D8E1F_1>>": "555-123-4567"
  },
  "detection_count": 2
}
```

**Response Fields:**
- `sanitized_content` (string|object): Content with PII masked using placeholders
- `mask_map` (object): Mapping of placeholders to original values
- `detection_count` (number): Number of PII entities detected

**Example with JSON content:**
```bash
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "user": "john@example.com",
      "message": "My phone is 555-123-4567"
    },
    "format": "json"
  }'
```

---

### Session-Based Sanitization

#### `POST /session/sanitize`

Sanitize content and store the mask map for later rehydration using a session ID.

**Request Body:**
```json
{
  "content": "Contact John at john@example.com",
  "session_id": "user_123_conversation_456",
  "format": "text",
  "regex_only": false,
  "pattern_packs": ["default"],
  "whitelist": [],
  "min_confidence": 0.9,
  "strict_validation": true
}
```

**Request Fields:**
- `content` (string|object, required): Content to sanitize
- `session_id` (string, required): Unique session identifier for later rehydration
- `format` (string, optional): Content format
- `regex_only` (boolean, optional): Use regex-only mode (default: false)
- `pattern_packs` (array, optional): Pattern packs to use
- `whitelist` (array, optional): Terms to exclude from masking
- `min_confidence` (number, optional): Minimum confidence threshold for NER
- `strict_validation` (boolean, optional): Enable strict validation (default: true)

**Response:**
```json
{
  "sanitized_content": "Contact John at <<EMAIL_7A9B2C_1>>",
  "session_id": "user_123_conversation_456",
  "storage_path": "rehydration_storage/user_123_conversation_456.json",
  "detection_count": 1
}
```

**Response Fields:**
- `sanitized_content` (string|object): Content with PII masked
- `session_id` (string): Session identifier for rehydration
- `storage_path` (string): Path where mask map is stored
- `detection_count` (number): Number of PII entities detected

---

## Rehydration Endpoints

### Basic Rehydration

#### `POST /rehydrate`

Restore original PII values using a provided mask map.

**Request Body:**
```json
{
  "masked_content": "Contact John at <<EMAIL_7A9B2C_1>>",
  "mask_map": {
    "<<EMAIL_7A9B2C_1>>": "john@example.com"
  }
}
```

**Request Fields:**
- `masked_content` (string|object, required): Content with PII placeholders
- `mask_map` (object, required): Mapping of placeholders to original values

**Response:**
```json
{
  "rehydrated_content": "Contact John at john@example.com",
  "placeholders_found": 1
}
```

**Response Fields:**
- `rehydrated_content` (string|object): Content with original PII restored
- `placeholders_found` (number): Number of placeholders processed

---

### Session-Based Rehydration

#### `POST /session/rehydrate`

Restore original PII values using a stored session mask map.

**Request Body:**
```json
{
  "masked_content": "Contact John at <<EMAIL_7A9B2C_1>>",
  "session_id": "user_123_conversation_456"
}
```

**Request Fields:**
- `masked_content` (string|object, required): Content with PII placeholders
- `session_id` (string, required): Session identifier

**Response:**
```json
{
  "rehydrated_content": "Contact John at john@example.com", 
  "placeholders_found": 1
}
```

**Response Fields:**
- `rehydrated_content` (string|object): Content with original PII restored
- `placeholders_found` (number): Number of placeholders processed

---

## Session Management

### List Sessions

#### `GET /sessions`

List all active rehydration sessions.

**Response:**
```json
{
  "sessions": [
    "user_123_conversation_456",
    "user_789_conversation_101"
  ],
  "count": 2
}
```

**Response Fields:**
- `sessions` (array): List of active session IDs
- `count` (number): Number of active sessions

---

### Delete Session

#### `DELETE /session/{session_id}`

Delete a stored session and cleanup its mask map.

**Path Parameters:**
- `session_id` (string, required): Session identifier to delete

**Response:**
```json
{
  "message": "Session 'user_123_conversation_456' deleted successfully"
}
```

**Error Response (404):**
```json
{
  "detail": "Session 'invalid_session' not found"
}
```

---

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid input, validation errors)
- `404` - Not Found (session not found)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "detail": "Error description"
}
```

### Common Error Scenarios

**Invalid JSON format:**
```json
{
  "detail": "Invalid request: JSON decode error"
}
```

**Invalid mask map:**
```json
{
  "detail": "Invalid mask map: Placeholder format mismatch"
}
```

**Session not found:**
```json
{
  "detail": "Session 'invalid_session' not found or expired"
}
```

**Rehydration compatibility issues:**
```json
{
  "detail": "Rehydration compatibility issues: Missing placeholders in mask map"
}
```

---

## Configuration

### Environment Variables

Configure the API using environment variables:

```bash
export API_HOST="0.0.0.0"          # Host to bind to
export API_PORT="8000"             # Port to listen on
export API_TITLE="MaskingEngine API"  # API title
export API_DESCRIPTION="Local-first PII sanitization service"
export API_VERSION="1.0.0"        # API version
export CORS_ORIGINS="*"            # CORS allowed origins (comma-separated)
```

### Starting the API

```bash
# Development mode (with auto-reload)
API_RELOAD=true python run_api.py

# Production mode
python run_api.py

# Custom host and port
API_HOST=127.0.0.1 API_PORT=9000 python run_api.py
```

---

## Complete Usage Examples

### Example 1: Basic Text Sanitization

```bash
# Sanitize text content
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Email me at john.doe@company.com or call 555-123-4567",
    "regex_only": true
  }'

# Response:
{
  "sanitized_content": "Email me at <<EMAIL_7A9B2C_1>> or call <<PHONE_4D8E1F_1>>",
  "mask_map": {
    "<<EMAIL_7A9B2C_1>>": "john.doe@company.com",
    "<<PHONE_4D8E1F_1>>": "555-123-4567"
  },
  "detection_count": 2
}
```

### Example 2: JSON Content with Whitelist

```bash
# Sanitize JSON with whitelist
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "user_email": "user@example.com",
      "support_email": "support@company.com",
      "phone": "555-123-4567"
    },
    "format": "json",
    "whitelist": ["support@company.com"]
  }'

# Response:
{
  "sanitized_content": {
    "user_email": "<<EMAIL_7A9B2C_1>>",
    "support_email": "support@company.com",
    "phone": "<<PHONE_4D8E1F_1>>"
  },
  "mask_map": {
    "<<EMAIL_7A9B2C_1>>": "user@example.com",
    "<<PHONE_4D8E1F_1>>": "555-123-4567"
  },
  "detection_count": 2
}
```

### Example 3: Session-Based Workflow

```bash
# Step 1: Sanitize with session
curl -X POST "http://localhost:8000/session/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Contact John Smith at john@example.com",
    "session_id": "chat_session_123"
  }'

# Step 2: Send sanitized content to LLM
# (external LLM processing with masked content)

# Step 3: Rehydrate LLM response
curl -X POST "http://localhost:8000/session/rehydrate" \
  -H "Content-Type: application/json" \
  -d '{
    "masked_content": "Response about <<EMAIL_7A9B2C_1>> request",
    "session_id": "chat_session_123"
  }'

# Step 4: Cleanup session
curl -X DELETE "http://localhost:8000/session/chat_session_123"
```

---

## Interactive Documentation

The API provides interactive documentation accessible at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Explore all endpoints interactively
- Test requests directly from the browser
- View detailed request/response schemas
- Download OpenAPI specification

---

## Production Considerations

### Security
- Add authentication middleware for production use
- Configure CORS origins appropriately
- Use HTTPS in production
- Implement rate limiting
- Add request/response logging

### Performance
- Use multiple worker processes with Gunicorn
- Configure memory limits for large content processing
- Monitor NER model memory usage
- Implement caching for frequently used patterns

### Monitoring
- Add health check endpoints for load balancers
- Monitor session storage cleanup
- Track API response times and error rates
- Monitor memory and CPU usage

### Example Production Deployment

```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  maskingengine.api.main:app
```