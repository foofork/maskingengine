# MaskingEngine Usage Examples

This document provides comprehensive examples of using MaskingEngine across different scenarios, interfaces, and integration patterns.

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Python SDK Examples](#python-sdk-examples)
3. [CLI Examples](#cli-examples)
4. [REST API Examples](#rest-api-examples)
5. [Framework Integration Examples](#framework-integration-examples)
6. [Advanced Use Cases](#advanced-use-cases)
7. [Production Examples](#production-examples)

---

## Quick Start Examples

### Basic Text Masking

```python
from maskingengine import Sanitizer

# Initialize sanitizer
sanitizer = Sanitizer()

# Mask PII in text
content = "Contact John Smith at john@example.com or call 555-123-4567"
masked_content, mask_map = sanitizer.sanitize(content)

print(f"Original: {content}")
print(f"Masked: {masked_content}")
print(f"Mask Map: {mask_map}")

# Output:
# Original: Contact John Smith at john@example.com or call 555-123-4567
# Masked: Contact John Smith at <<EMAIL_7A9B2C_1>> or call <<PHONE_4D8E1F_1>>
# Mask Map: {'<<EMAIL_7A9B2C_1>>': 'john@example.com', '<<PHONE_4D8E1F_1>>': '555-123-4567'}
```

### Basic Rehydration

```python
from maskingengine import Rehydrator

# Rehydrate masked content
rehydrator = Rehydrator()
original_content = rehydrator.rehydrate(masked_content, mask_map)

print(f"Rehydrated: {original_content}")
# Output: Rehydrated: Contact John Smith at john@example.com or call 555-123-4567
```

---

## Python SDK Examples

### Configuration Options

```python
from maskingengine import Sanitizer, Config

# Custom configuration
config = Config(
    pattern_packs=["default", "enterprise"],  # Use multiple pattern packs
    whitelist=["support@company.com"],        # Exclude certain terms
    regex_only=True,                          # Fast mode (regex only)
    strict_validation=True,                   # Enable validation (Luhn check, etc.)
    min_confidence=0.9                        # NER confidence threshold
)

sanitizer = Sanitizer(config)
content = "Contact support@company.com or john@personal.com"
masked, mask_map = sanitizer.sanitize(content)

print(f"Masked: {masked}")
# Output: Contact support@company.com or <<EMAIL_7A9B2C_1>>
# (support@company.com is whitelisted)
```

### JSON Content Processing

```python
import json
from maskingengine import Sanitizer

# JSON data with PII
data = {
    "user_profile": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-123-4567",
        "address": {
            "street": "123 Main St",
            "city": "Anytown"
        }
    },
    "metadata": {
        "created": "2024-01-15",
        "version": 1.0
    }
}

sanitizer = Sanitizer()
masked_data, mask_map = sanitizer.sanitize(data, format="json")

print("Original JSON:")
print(json.dumps(data, indent=2))

print("\\nMasked JSON:")
print(json.dumps(masked_data, indent=2))

print("\\nMask Map:")
print(json.dumps(mask_map, indent=2))

# Output shows JSON structure preserved with PII masked
```

### HTML Content Processing

```python
from maskingengine import Sanitizer

html_content = """
<html>
<body>
    <div class="contact-info">
        <h2>Contact Information</h2>
        <p>Email: <a href="mailto:john@example.com">john@example.com</a></p>
        <p>Phone: <span class="phone">555-123-4567</span></p>
        <p>Address: 123 Main Street, Anytown</p>
    </div>
</body>
</html>
"""

sanitizer = Sanitizer()
masked_html, mask_map = sanitizer.sanitize(html_content, format="html")

print("Masked HTML:")
print(masked_html)
# HTML structure preserved, only text content masked
```

### Session-Based Workflow

```python
from maskingengine import Sanitizer, RehydrationPipeline, RehydrationStorage

# Setup rehydration pipeline
sanitizer = Sanitizer()
storage = RehydrationStorage()
pipeline = RehydrationPipeline(sanitizer, storage)

# Step 1: Sanitize with session
content = "User john@example.com requested account information"
session_id = "user_session_123"

masked_content, storage_path = pipeline.sanitize_with_session(
    content, session_id
)

print(f"Masked: {masked_content}")
print(f"Session stored at: {storage_path}")

# Step 2: Process with external service (simulated)
external_response = f"Processing request for {masked_content}"

# Step 3: Rehydrate the response
rehydrated_response = pipeline.rehydrate_with_session(
    external_response, session_id
)

print(f"Final response: {rehydrated_response}")

# Step 4: Cleanup session
pipeline.complete_session(session_id)
```

### Error Handling

```python
from maskingengine import Sanitizer, Config, Rehydrator

# Graceful error handling
try:
    config = Config(pattern_packs=["nonexistent_pack"])
    sanitizer = Sanitizer(config)
    # Will fall back to default patterns with warning
    
    masked, mask_map = sanitizer.sanitize("test@example.com")
    print(f"Processing succeeded: {masked}")
    
except Exception as e:
    print(f"Error occurred: {e}")

# Rehydration validation
rehydrator = Rehydrator()
invalid_mask_map = {"<<INVALID>>": "test"}

is_valid, issues = rehydrator.validate_mask_map(invalid_mask_map)
if not is_valid:
    print(f"Validation issues: {issues}")
```

---

## CLI Examples

### Basic File Processing

```bash
# Process a text file
echo "Contact john@example.com or call 555-123-4567" > input.txt
maskingengine mask input.txt -o output.txt

# View results
cat output.txt
# Output: Contact <<EMAIL_7A9B2C_1>> or call <<PHONE_4D8E1F_1>>
```

### Fast Processing with Regex-Only Mode

```bash
# Use regex-only mode for maximum speed
maskingengine mask large_file.txt --regex-only -o masked_file.txt

# Process from stdin
echo "Email: user@company.com" | maskingengine mask --stdin --regex-only
# Output: Email: <<EMAIL_7A9B2C_1>>
```

### Custom Pattern Packs

```bash
# Use custom pattern pack
maskingengine mask input.txt --pattern-packs enterprise -o output.txt

# Use multiple pattern packs
maskingengine mask input.txt --pattern-packs default enterprise healthcare -o output.txt

# With whitelist
maskingengine mask input.txt \
  --whitelist "support@company.com" \
  --whitelist "noreply@company.com" \
  -o output.txt
```

### JSON File Processing

```bash
# Create sample JSON file
cat > data.json << EOF
{
  "users": [
    {"name": "John", "email": "john@example.com"},
    {"name": "Jane", "email": "jane@example.com"}
  ]
}
EOF

# Process JSON file
maskingengine mask data.json --format json -o masked_data.json

# View masked JSON
cat masked_data.json
```

### Session-Based CLI Workflow

```bash
# Step 1: Sanitize with session
echo "User john@example.com requested data" | \
  maskingengine session-sanitize --stdin user_session_456 -o masked.txt

# Step 2: View masked content
cat masked.txt

# Step 3: Simulate external processing and rehydrate
echo "Processing request for <<EMAIL_7A9B2C_1>>" | \
  maskingengine session-rehydrate --stdin user_session_456

# Step 4: List active sessions
maskingengine sessions

# Step 5: Cleanup
maskingengine session-rehydrate masked.txt user_session_456 --cleanup
```

### Batch Processing

```bash
# Process multiple files
for file in *.txt; do
  maskingengine mask "$file" --regex-only -o "masked_$file"
done

# Process with pattern matching
find ./data -name "*.json" -exec maskingengine mask {} --format json -o {}.masked \\;
```

### Testing and Validation

```bash
# Test MaskingEngine installation
maskingengine test

# Test with custom session
maskingengine test --session-id test_session_123

# Session cleanup
maskingengine cleanup-sessions --max-age-hours 24
```

---

## REST API Examples

### Basic API Usage

```bash
# Start the API server
python run_api.py &

# Basic health check
curl -X GET "http://localhost:8000/health"
```

#### Text Sanitization

```bash
# Simple text masking
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Contact john@example.com or call 555-123-4567"
  }'

# Response:
{
  "sanitized_content": "Contact <<EMAIL_7A9B2C_1>> or call <<PHONE_4D8E1F_1>>",
  "mask_map": {
    "<<EMAIL_7A9B2C_1>>": "john@example.com",
    "<<PHONE_4D8E1F_1>>": "555-123-4567"
  },
  "detection_count": 2
}
```

#### JSON Content Processing

```bash
# Process JSON data
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "user": "john@example.com",
      "phone": "555-123-4567",
      "metadata": {"active": true}
    },
    "format": "json"
  }'
```

#### Advanced Configuration

```bash
# Use custom configuration
curl -X POST "http://localhost:8000/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Contact support@company.com or john@personal.com",
    "regex_only": true,
    "pattern_packs": ["default"],
    "whitelist": ["support@company.com"],
    "strict_validation": true
  }'
```

### Session-Based API Workflow

```bash
# Step 1: Sanitize with session
curl -X POST "http://localhost:8000/session/sanitize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User john@example.com requested account data",
    "session_id": "api_session_789"
  }'

# Response includes session_id and storage_path

# Step 2: Rehydrate using session
curl -X POST "http://localhost:8000/session/rehydrate" \
  -H "Content-Type: application/json" \
  -d '{
    "masked_content": "Processing <<EMAIL_7A9B2C_1>> request",
    "session_id": "api_session_789"
  }'

# Step 3: List sessions
curl -X GET "http://localhost:8000/sessions"

# Step 4: Delete session
curl -X DELETE "http://localhost:8000/session/api_session_789"
```

### Basic Rehydration

```bash
# Rehydrate with explicit mask map
curl -X POST "http://localhost:8000/rehydrate" \
  -H "Content-Type: application/json" \
  -d '{
    "masked_content": "Contact <<EMAIL_7A9B2C_1>> for details",
    "mask_map": {
      "<<EMAIL_7A9B2C_1>>": "john@example.com"
    }
  }'
```

---

## Framework Integration Examples

### LangChain Integration

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from maskingengine import Sanitizer, RehydrationPipeline, RehydrationStorage

class PrivacyAwareTextSplitter(RecursiveCharacterTextSplitter):
    """LangChain text splitter with PII masking."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sanitizer = Sanitizer()
    
    def split_text(self, text: str) -> list[str]:
        # Mask PII before splitting
        masked_text, _ = self.sanitizer.sanitize(text)
        return super().split_text(masked_text)
    
    def create_documents(self, texts: list[str], metadatas: list[dict] = None) -> list[Document]:
        # Process each document
        masked_texts = []
        mask_maps = []
        
        for text in texts:
            masked, mask_map = self.sanitizer.sanitize(text)
            masked_texts.append(masked)
            mask_maps.append(mask_map)
        
        # Create documents with masked content
        documents = super().create_documents(masked_texts, metadatas)
        
        # Store mask maps in metadata
        for doc, mask_map in zip(documents, mask_maps):
            doc.metadata['mask_map'] = mask_map
        
        return documents

# Usage example
text_splitter = PrivacyAwareTextSplitter(chunk_size=1000)
documents = text_splitter.create_documents([
    "Contact John at john@example.com for project details."
])

# Documents now contain masked content with mask maps in metadata
```

### LangChain Chain Integration

```python
from langchain.chains.base import Chain
from langchain.schema import BaseLanguageModel
from maskingengine import RehydrationPipeline, Sanitizer, RehydrationStorage

class PrivacyChain(Chain):
    """LangChain chain with automatic PII masking/rehydration."""
    
    llm: BaseLanguageModel
    input_key: str = "input"
    output_key: str = "output"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        sanitizer = Sanitizer()
        storage = RehydrationStorage()
        self.pipeline = RehydrationPipeline(sanitizer, storage)
    
    @property
    def input_keys(self) -> list[str]:
        return [self.input_key]
    
    @property
    def output_keys(self) -> list[str]:
        return [self.output_key]
    
    def _call(self, inputs: dict) -> dict:
        input_text = inputs[self.input_key]
        session_id = f"chain_session_{hash(input_text)}"
        
        # Step 1: Mask PII
        masked_input, _ = self.pipeline.sanitize_with_session(
            input_text, session_id
        )
        
        # Step 2: Process with LLM
        llm_response = self.llm.predict(masked_input)
        
        # Step 3: Rehydrate response
        final_response = self.pipeline.rehydrate_with_session(
            llm_response, session_id
        )
        
        # Cleanup
        self.pipeline.complete_session(session_id)
        
        return {self.output_key: final_response}

# Usage
from langchain.llms import OpenAI

privacy_chain = PrivacyChain(llm=OpenAI(temperature=0))
result = privacy_chain({
    "input": "Summarize the account for john@example.com"
})
print(result["output"])
```

### Pandas Integration

```python
import pandas as pd
from maskingengine import Sanitizer, RehydrationPipeline, RehydrationStorage

# Sample DataFrame with PII
df = pd.DataFrame({
    'user_id': [1, 2, 3],
    'email': ['john@example.com', 'jane@company.com', 'bob@test.org'],
    'phone': ['555-123-4567', '555-987-6543', '555-456-7890'],
    'notes': [
        'Customer called about billing',
        'Support ticket for email issue',
        'Sales inquiry about products'
    ]
})

print("Original DataFrame:")
print(df)

# Method 1: Simple masking
sanitizer = Sanitizer()

def mask_text(text):
    if pd.isna(text):
        return text
    masked, _ = sanitizer.sanitize(str(text))
    return masked

# Apply masking to specific columns
df_masked = df.copy()
df_masked['email'] = df['email'].apply(mask_text)
df_masked['phone'] = df['phone'].apply(mask_text)
df_masked['notes'] = df['notes'].apply(mask_text)

print("\\nMasked DataFrame:")
print(df_masked)

# Method 2: Session-based masking for rehydration
storage = RehydrationStorage()
pipeline = RehydrationPipeline(sanitizer, storage)

def mask_with_session(text, session_id):
    if pd.isna(text):
        return text
    masked, _ = pipeline.sanitize_with_session(str(text), session_id)
    return masked

# Create session-based masked DataFrame
df_session_masked = df.copy()
session_id = "dataframe_session_001"

for col in ['email', 'phone', 'notes']:
    df_session_masked[col] = df[col].apply(
        lambda x: mask_with_session(x, f"{session_id}_{col}")
    )

print("\\nSession-masked DataFrame:")
print(df_session_masked)

# Later rehydration
def rehydrate_column(masked_df, original_df, column, session_id):
    def rehydrate_cell(masked_text):
        if pd.isna(masked_text):
            return masked_text
        return pipeline.rehydrate_with_session(
            str(masked_text), f"{session_id}_{column}"
        )
    
    return masked_df[column].apply(rehydrate_cell)

# Rehydrate specific column
df_session_masked['email_rehydrated'] = rehydrate_column(
    df_session_masked, df, 'email', session_id
)

print("\\nRehydrated email column:")
print(df_session_masked[['email', 'email_rehydrated']])
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from maskingengine import Sanitizer, Config, RehydrationPipeline, RehydrationStorage

app = FastAPI(title="Privacy-Aware API")

# Global instances
sanitizer = Sanitizer()
storage = RehydrationStorage()
pipeline = RehydrationPipeline(sanitizer, storage)

class TextRequest(BaseModel):
    content: str
    session_id: Optional[str] = None
    mask_pii: bool = True

class TextResponse(BaseModel):
    processed_content: str
    session_id: Optional[str] = None

@app.post("/process", response_model=TextResponse)
async def process_text(request: TextRequest):
    """Process text with optional PII masking."""
    
    if request.mask_pii and request.session_id:
        # Session-based masking
        masked_content, _ = pipeline.sanitize_with_session(
            request.content, request.session_id
        )
        
        # Simulate processing (e.g., AI analysis)
        processed = f"Processed: {masked_content}"
        
        # Rehydrate before returning
        final_content = pipeline.rehydrate_with_session(
            processed, request.session_id
        )
        
        return TextResponse(
            processed_content=final_content,
            session_id=request.session_id
        )
    
    elif request.mask_pii:
        # Simple masking without session
        masked_content, _ = sanitizer.sanitize(request.content)
        processed = f"Processed: {masked_content}"
        
        return TextResponse(processed_content=processed)
    
    else:
        # No masking
        processed = f"Processed: {request.content}"
        return TextResponse(processed_content=processed)

@app.get("/health")
async def health_check():
    """Health check with PII masking capability test."""
    test_content = "test@example.com"
    masked, _ = sanitizer.sanitize(test_content)
    
    return {
        "status": "healthy",
        "masking_functional": masked != test_content
    }

# Usage example
# POST /process
# {
#   "content": "User john@example.com needs assistance",
#   "session_id": "user_session_123",
#   "mask_pii": true
# }
```

---

## Advanced Use Cases

### Multi-Language Content Processing

```python
from maskingengine import Sanitizer, Config

# Create sanitizer with multi-language patterns
config = Config(pattern_packs=["default"])  # Includes international patterns
sanitizer = Sanitizer(config)

# Process content in different languages
contents = {
    "English": "Contact John at john@example.com or +1-555-123-4567",
    "French": "Contactez Marie à marie@exemple.fr ou 01 23 45 67 89",
    "German": "Kontaktieren Sie Hans unter hans@beispiel.de oder +49 123 456789",
    "Spanish": "Contacte a Ana en ana@ejemplo.es o 91 123 45 67"
}

for language, content in contents.items():
    masked, mask_map = sanitizer.sanitize(content)
    print(f"{language}: {masked}")
    print(f"Detected: {list(mask_map.keys())}")
    print()
```

### Large Document Processing

```python
import io
from maskingengine import Sanitizer

def process_large_document(file_path, chunk_size=1024*1024):  # 1MB chunks
    """Process large documents in chunks to manage memory."""
    
    sanitizer = Sanitizer()
    all_mask_maps = {}
    
    with open(file_path, 'r', encoding='utf-8') as infile:
        with open(f"masked_{file_path}", 'w', encoding='utf-8') as outfile:
            
            chunk_num = 0
            while True:
                chunk = infile.read(chunk_size)
                if not chunk:
                    break
                
                # Process chunk
                masked_chunk, mask_map = sanitizer.sanitize(chunk)
                
                # Merge mask maps
                all_mask_maps.update(mask_map)
                
                # Write masked chunk
                outfile.write(masked_chunk)
                
                chunk_num += 1
                print(f"Processed chunk {chunk_num}, found {len(mask_map)} PII entities")
    
    # Save combined mask map
    import json
    with open(f"mask_map_{file_path}.json", 'w') as f:
        json.dump(all_mask_maps, f, indent=2)
    
    print(f"Total PII entities found: {len(all_mask_maps)}")

# Usage
process_large_document("large_document.txt")
```

### Real-Time Stream Processing

```python
import asyncio
from maskingengine import Sanitizer, RehydrationPipeline, RehydrationStorage

class StreamProcessor:
    """Real-time stream processing with PII masking."""
    
    def __init__(self):
        self.sanitizer = Sanitizer()
        self.storage = RehydrationStorage()
        self.pipeline = RehydrationPipeline(self.sanitizer, self.storage)
    
    async def process_stream(self, input_stream, output_stream):
        """Process incoming stream data with PII masking."""
        
        buffer = ""
        session_counter = 0
        
        async for chunk in input_stream:
            buffer += chunk
            
            # Process complete lines
            while '\\n' in buffer:
                line, buffer = buffer.split('\\n', 1)
                
                if line.strip():
                    session_id = f"stream_session_{session_counter}"
                    session_counter += 1
                    
                    # Mask PII
                    masked_line, _ = self.pipeline.sanitize_with_session(
                        line, session_id
                    )
                    
                    # Send to output stream
                    await output_stream.send(f"{masked_line}\\n")
                    
                    # Optional: Store session for later rehydration
                    print(f"Processed line with session {session_id}")

# Usage example
async def main():
    processor = StreamProcessor()
    
    # Simulate input stream
    async def input_generator():
        messages = [
            "User john@example.com logged in",
            "Payment from card 4111-1111-1111-1111",
            "Call customer at 555-123-4567"
        ]
        for msg in messages:
            yield msg + "\\n"
            await asyncio.sleep(1)
    
    # Simulate output stream
    class OutputCollector:
        def __init__(self):
            self.messages = []
        
        async def send(self, message):
            self.messages.append(message)
            print(f"Output: {message.strip()}")
    
    output = OutputCollector()
    await processor.process_stream(input_generator(), output)

# Run the example
# asyncio.run(main())
```

---

## Production Examples

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install MaskingEngine
RUN pip install maskingengine

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "maskingengine.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  maskingengine:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - CORS_ORIGINS=*
    volumes:
      - ./rehydration_storage:/app/rehydration_storage
      - ./custom_patterns:/app/patterns
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - maskingengine
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maskingengine
  labels:
    app: maskingengine
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
        env:
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: storage
          mountPath: /app/rehydration_storage
        - name: patterns
          mountPath: /app/custom_patterns
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: maskingengine-storage
      - name: patterns
        configMap:
          name: custom-patterns

---
apiVersion: v1
kind: Service
metadata:
  name: maskingengine-service
spec:
  selector:
    app: maskingengine
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: maskingengine-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Load Testing

```python
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

async def load_test_api():
    """Load test the MaskingEngine API."""
    
    test_payloads = [
        {"content": "Contact john@example.com or call 555-123-4567"},
        {"content": {"user": "jane@company.com", "phone": "555-987-6543"}},
        {"content": "SSN: 123-45-6789, Card: 4111-1111-1111-1111"},
    ]
    
    async def make_request(session, payload):
        start_time = time.time()
        try:
            async with session.post(
                "http://localhost:8000/sanitize",
                json=payload
            ) as response:
                await response.json()
                return time.time() - start_time, response.status
        except Exception as e:
            return time.time() - start_time, 0
    
    # Run load test
    concurrent_users = 50
    requests_per_user = 20
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for user in range(concurrent_users):
            for req in range(requests_per_user):
                payload = test_payloads[req % len(test_payloads)]
                tasks.append(make_request(session, payload))
        
        print(f"Starting load test: {len(tasks)} requests...")
        start_time = time.time()
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Analyze results
        response_times = [r[0] for r in results]
        status_codes = [r[1] for r in results]
        
        successful_requests = sum(1 for code in status_codes if code == 200)
        
        print(f"\\nLoad Test Results:")
        print(f"Total requests: {len(results)}")
        print(f"Successful requests: {successful_requests}")
        print(f"Success rate: {successful_requests/len(results)*100:.1f}%")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests per second: {len(results)/total_time:.1f}")
        print(f"Average response time: {statistics.mean(response_times)*1000:.1f}ms")
        print(f"95th percentile: {statistics.quantiles(response_times, n=20)[18]*1000:.1f}ms")

# Run load test
# asyncio.run(load_test_api())
```

### Monitoring and Logging

```python
import logging
import time
from functools import wraps
from maskingengine import Sanitizer, Config

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('maskingengine_monitor')

class MonitoredSanitizer:
    """Wrapper around Sanitizer with monitoring and metrics."""
    
    def __init__(self, config=None):
        self.sanitizer = Sanitizer(config)
        self.metrics = {
            'total_requests': 0,
            'total_processing_time': 0,
            'total_pii_detected': 0,
            'errors': 0
        }
    
    def sanitize(self, content, format=None, session_id=None):
        """Monitored sanitize method."""
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        try:
            masked_content, mask_map = self.sanitizer.sanitize(content, format)
            
            processing_time = time.time() - start_time
            self.metrics['total_processing_time'] += processing_time
            self.metrics['total_pii_detected'] += len(mask_map)
            
            logger.info(
                f"Sanitization completed",
                extra={
                    'session_id': session_id,
                    'processing_time_ms': processing_time * 1000,
                    'pii_entities_found': len(mask_map),
                    'content_length': len(str(content)),
                    'format': format or 'auto'
                }
            )
            
            return masked_content, mask_map
            
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(
                f"Sanitization failed: {str(e)}",
                extra={
                    'session_id': session_id,
                    'error_type': type(e).__name__,
                    'content_length': len(str(content)) if content else 0
                }
            )
            raise
    
    def get_metrics(self):
        """Get current metrics."""
        if self.metrics['total_requests'] > 0:
            avg_processing_time = (
                self.metrics['total_processing_time'] / 
                self.metrics['total_requests']
            )
            avg_pii_per_request = (
                self.metrics['total_pii_detected'] / 
                self.metrics['total_requests']
            )
        else:
            avg_processing_time = 0
            avg_pii_per_request = 0
        
        return {
            **self.metrics,
            'average_processing_time_ms': avg_processing_time * 1000,
            'average_pii_per_request': avg_pii_per_request,
            'error_rate': self.metrics['errors'] / max(self.metrics['total_requests'], 1)
        }

# Usage
monitored_sanitizer = MonitoredSanitizer()

# Process some requests
test_contents = [
    "Contact john@example.com",
    {"user": "jane@company.com", "phone": "555-123-4567"},
    "Invalid content that might cause errors"
]

for i, content in enumerate(test_contents):
    try:
        masked, mask_map = monitored_sanitizer.sanitize(
            content, 
            session_id=f"test_session_{i}"
        )
    except Exception:
        pass  # Error already logged

# View metrics
print("\\nMetrics:")
import json
print(json.dumps(monitored_sanitizer.get_metrics(), indent=2))
```

## LLM Integration Best Practices

### Prompting LLMs to Preserve Placeholders

**Critical Success Factor**: The LLM must preserve placeholder tokens exactly for successful rehydration.

#### ✅ **Effective Prompt Template:**
```python
def create_llm_prompt_with_placeholder_preservation(user_content: str) -> str:
    return f"""You are a helpful assistant. Please respond to the user's request below.

IMPORTANT: The text contains placeholder tokens in the format <<TYPE_HASH_INDEX>> (like <<EMAIL_7A9B2C_1>>). 
You MUST preserve these tokens EXACTLY as they appear in your response. Do not modify, replace, or remove them.

User request: {user_content}

Remember: Keep all placeholder tokens (<<...>>) exactly as shown."""
```

#### 📝 **Prompt Examples by Use Case:**

**Summarization:**
```
Please summarize the following text. 

IMPORTANT: Keep all privacy tokens (<<TYPE_HASH_INDEX>>) unchanged in your summary.

Text to summarize: {content}
```

**Translation:**
```
Translate this text to Spanish.

CRITICAL RULE: Do NOT translate the privacy tokens <<TYPE_HASH_INDEX>>. 
Keep them exactly as they appear in the original.

Original text: {content}
```

**Code Generation:**
```
Generate code based on this description.

MANDATORY: If the description contains <<TYPE_HASH_INDEX>> tokens, 
include them exactly as placeholder values in your code.

Description: {content}
```

#### ⚠️ **Common Mistakes to Avoid:**

| ❌ **Don't Do** | ✅ **Do Instead** |
|----------------|------------------|
| "Summarize: Contact [REDACTED] for info" | "Summarize (preserve <<EMAIL_7A9B2C_1>> exactly): Contact <<EMAIL_7A9B2C_1>> for info" |
| "What does <<EMAIL_7A9B2C_1>> represent?" | Treat placeholders as opaque tokens to preserve |
| Using unclear formats like [REDACTED] | Use distinctive <<TYPE_HASH_INDEX>> format |
| No validation of preservation | Always validate placeholders before rehydration |

#### 🔍 **Validation Example:**
```python
def validate_placeholder_preservation(original_masked: str, llm_response: str) -> bool:
    import re
    placeholder_pattern = r'<<[A-Z0-9_]+_[A-F0-9]{6}_\d+>>'
    
    original_placeholders = set(re.findall(placeholder_pattern, original_masked))
    response_placeholders = set(re.findall(placeholder_pattern, llm_response))
    
    missing = original_placeholders - response_placeholders
    if missing:
        print(f"⚠️ Missing placeholders: {missing}")
        return False
    return True
```

#### 🏭 **Production Integration Pattern:**
```python
def safe_llm_processing(user_input: str, session_id: str) -> str:
    # 1. Mask PII
    masked_content, _ = pipeline.sanitize_with_session(user_input, session_id)
    
    # 2. Create preservation prompt
    prompt = create_llm_prompt_with_placeholder_preservation(masked_content)
    
    # 3. Call LLM
    llm_response = your_llm_client.complete(prompt)
    
    # 4. Validate preservation
    if not validate_placeholder_preservation(masked_content, llm_response):
        raise ValueError("LLM failed to preserve placeholders")
    
    # 5. Rehydrate safely
    return pipeline.rehydrate_with_session(llm_response, session_id)
```

**📖 For complete examples, see [`examples/llm_integration_example.py`](../examples/llm_integration_example.py)**

---

This comprehensive set of examples demonstrates the versatility and power of MaskingEngine across different use cases, from simple text processing to complex production deployments. Each example includes practical code that can be adapted to specific requirements.