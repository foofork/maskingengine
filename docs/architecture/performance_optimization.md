# Performance Optimization Strategies

## 1. Performance Targets and Constraints

### 1.1 Target Metrics
```python
PERFORMANCE_TARGETS = {
    # Latency (P95)
    'small_doc_1kb': 10,     # 10ms
    'medium_doc_10kb': 50,   # 50ms  
    'large_doc_100kb': 100,  # 100ms
    
    # Throughput
    'concurrent_docs': 100,  # 100 docs/second
    
    # Memory
    'baseline_memory': 20,   # 20MB without NER
    'max_memory': 100,       # 100MB with NER loaded
    
    # CPU
    'single_thread': True,   # No threading complexity
    'cpu_utilization': 90    # Max 90% CPU usage
}
```

### 1.2 Critical Path Analysis
```
Total Budget: 100ms for 100KB document

Parse:     2ms  (2%)   - Format detection + text extraction
Regex:     20ms (20%)  - Pattern matching across all types  
NER:       60ms (60%)  - Model inference (if enabled)
Merge:     3ms  (3%)   - Deduplication and conflict resolution
Mask:      5ms  (5%)   - String replacement operations
Reconstruct: 10ms (10%) - JSON/HTML structure rebuilding
```

## 2. Regex Optimization Strategies

### 2.1 Pattern Compilation and Ordering
```python
class OptimizedRegexDetector:
    def __init__(self, patterns):
        # Pre-compile all patterns at init (not per-call)
        self.compiled_patterns = self._compile_optimized(patterns)
        
        # Order by expected frequency (email/phone first)
        self.pattern_order = ['EMAIL', 'PHONE_US', 'SSN', 'CREDIT_CARD']
    
    def _compile_optimized(self, patterns):
        """Optimize regex patterns for performance"""
        optimized = {}
        for name, pattern in patterns.items():
            # Use possessive quantifiers to prevent backtracking
            pattern = pattern.replace('+', '+?').replace('*', '*?')
            
            # Add word boundaries where appropriate
            if name in ['SSN', 'CREDIT_CARD']:
                pattern = f'\\b{pattern}\\b'
            
            # Compile with optimization flags
            optimized[name] = re.compile(
                pattern, 
                re.IGNORECASE | re.MULTILINE
            )
        return optimized
    
    def detect(self, text: str) -> List[Detection]:
        """Optimized detection with early termination"""
        detections = []
        
        # Quick length check
        if len(text) > 100000:  # >100KB
            # Process in chunks to avoid catastrophic backtracking
            return self._detect_chunked(text)
        
        # Run patterns in order of frequency
        for pii_type in self.pattern_order:
            pattern = self.compiled_patterns[pii_type]
            
            # Use finditer for memory efficiency
            for match in pattern.finditer(text):
                # Early validation for expensive patterns
                if pii_type == 'CREDIT_CARD':
                    if not self._luhn_check(match.group()):
                        continue
                
                detections.append(Detection(
                    type=pii_type,
                    start=match.start(),
                    end=match.end(),
                    text=match.group()
                ))
        
        return detections
```

### 2.2 Pattern Optimization Techniques
```python
# Original slow patterns
SLOW_PATTERNS = {
    'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'PHONE': r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
}

# Optimized fast patterns  
FAST_PATTERNS = {
    # Atomic grouping prevents backtracking
    'EMAIL': r'[a-zA-Z0-9._%+-]++@[a-zA-Z0-9.-]++\.[a-zA-Z]{2,6}',
    
    # Non-capturing groups + possessive quantifiers
    'PHONE_US': r'(?:\+?1[-.\s]?+)?+\(?+[0-9]{3}\)?+[-.\s]?+[0-9]{3}[-.\s]?+[0-9]{4}',
    
    # Exact length matching for fixed formats
    'SSN': r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b',
    
    # Simplified credit card with length check
    'CREDIT_CARD': r'\b[0-9]{4}[\s-]?+[0-9]{4}[\s-]?+[0-9]{4}[\s-]?+[0-9]{4}\b'
}
```

### 2.3 Chunked Processing for Large Documents
```python
def _detect_chunked(self, text: str, chunk_size: int = 50000) -> List[Detection]:
    """Process large documents in chunks to prevent timeouts"""
    detections = []
    
    # Overlap chunks to catch PII at boundaries
    overlap = 1000  # 1KB overlap
    
    for i in range(0, len(text), chunk_size - overlap):
        chunk_end = min(i + chunk_size, len(text))
        chunk = text[i:chunk_end]
        
        # Detect in chunk
        chunk_detections = self._detect_single_chunk(chunk)
        
        # Adjust offsets to global position
        for detection in chunk_detections:
            detections.append(Detection(
                type=detection.type,
                start=detection.start + i,
                end=detection.end + i,
                text=detection.text
            ))
    
    # Remove duplicates from overlapping regions
    return self._deduplicate_overlaps(detections)
```

## 3. NER Optimization Strategies

### 3.1 Lazy Loading and Model Optimization
```python
class OptimizedNERDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self._model = None  # Lazy loaded
        self._model_loading = False
        self._load_lock = threading.Lock()
    
    @property
    def model(self):
        """Thread-safe lazy loading"""
        if self._model is None and not self._model_loading:
            with self._load_lock:
                if self._model is None:  # Double-check
                    self._model_loading = True
                    self._model = self._load_optimized_model()
                    self._model_loading = False
        return self._model
    
    def _load_optimized_model(self):
        """Load minimal NER model with only required components"""
        import spacy
        
        # Load with minimal pipeline
        nlp = spacy.load(self.model_path, disable=['lemmatizer', 'textcat'])
        
        # Optimize for speed over accuracy
        nlp.max_length = 100000  # Limit document size
        
        # Disable unnecessary features
        for pipe_name in nlp.pipe_names:
            pipe = nlp.get_pipe(pipe_name)  
            if hasattr(pipe, 'cfg'):
                pipe.cfg['beam_width'] = 1  # Greedy decoding
        
        return nlp
    
    def detect(self, text: str) -> List[Detection]:
        """Optimized NER detection with batching"""
        if not self.model:
            return []  # Skip if model failed to load
        
        # Quick filters to avoid NER overhead
        if len(text) < 10:  # Too short
            return []
        
        if not self._has_potential_entities(text):
            return []  # No capitalized words
        
        # Process with timeout
        with timeout(seconds=0.5):  # 500ms max for NER
            doc = self.model(text)
            
            detections = []
            for ent in doc.ents:
                # Filter by entity type and confidence
                if (ent.label_ in ['PERSON', 'ORG', 'GPE'] and 
                    len(ent.text) > 2):  # Filter short matches
                    
                    detections.append(Detection(
                        type=ent.label_,
                        start=ent.start_char,
                        end=ent.end_char, 
                        text=ent.text
                    ))
            
            return detections
    
    def _has_potential_entities(self, text: str) -> bool:
        """Quick heuristic check before expensive NER"""
        # Look for capitalized words (potential proper nouns)
        return re.search(r'\b[A-Z][a-z]+', text) is not None
```

### 3.2 NER Batching and Caching
```python
class BatchingNERDetector:
    def __init__(self, model_path, batch_size=10):
        self.model_path = model_path
        self.batch_size = batch_size
        self.cache = LRUCache(maxsize=1000)
        
    def detect_batch(self, texts: List[str]) -> List[List[Detection]]:
        """Process multiple texts in batch for efficiency"""
        # Check cache first
        cached_results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.cache:
                cached_results.append((i, self.cache[text_hash]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Process uncached texts in batch
        if uncached_texts:
            batch_results = self._process_batch(uncached_texts)
            
            # Cache results
            for text, result in zip(unccached_texts, batch_results):
                text_hash = hashlib.md5(text.encode()).hexdigest()
                self.cache[text_hash] = result
            
            # Merge with cached results
            all_results = [None] * len(texts)
            for i, result in cached_results:
                all_results[i] = result
            for i, result in zip(uncached_indices, batch_results):
                all_results[i] = result
                
            return all_results
        else:
            # All cached
            result = [None] * len(texts)
            for i, cached_result in cached_results:
                result[i] = cached_result
            return result
```

## 4. Memory Optimization

### 4.1 Memory-Efficient String Operations
```python
class MemoryEfficientMasker:
    def mask(self, text: str, detections: List[Detection]) -> str:
        """Memory-efficient masking using minimal allocations"""
        if not detections:
            return text
        
        # Sort detections in reverse order (right to left)
        sorted_detections = sorted(detections, key=lambda d: d.start, reverse=True)
        
        # Use bytearray for in-place modifications (if text is ASCII)
        if text.isascii():
            return self._mask_ascii_optimized(text, sorted_detections)
        else:
            return self._mask_unicode_safe(text, sorted_detections)
    
    def _mask_ascii_optimized(self, text: str, detections: List[Detection]) -> str:
        """Optimized ASCII-only masking"""
        text_bytes = bytearray(text.encode('ascii'))
        
        for detection in detections:
            placeholder = self._get_placeholder(detection.type).encode('ascii')
            
            # Replace in-place
            start_byte = detection.start
            end_byte = detection.end
            text_bytes[start_byte:end_byte] = placeholder
        
        return text_bytes.decode('ascii')
    
    def _mask_unicode_safe(self, text: str, detections: List[Detection]) -> str:
        """Unicode-safe masking with minimal string copies"""
        # Use string builder pattern
        parts = []
        last_end = 0
        
        # Process detections left to right (reverse sorted)
        for detection in reversed(detections):
            # Add text before detection
            parts.append(text[last_end:detection.start])
            
            # Add placeholder
            parts.append(self._get_placeholder(detection.type))
            
            last_end = detection.end
        
        # Add remaining text
        parts.append(text[last_end:])
        
        return ''.join(parts)
```

### 4.2 Object Pool and Reuse
```python
class DetectionPool:
    """Object pool for Detection instances to reduce GC pressure"""
    def __init__(self, initial_size=100):
        self._pool = [Detection('', 0, 0, '') for _ in range(initial_size)]
        self._available = list(range(initial_size))
    
    def get_detection(self, type_: str, start: int, end: int, text: str) -> Detection:
        """Get a detection object from pool or create new"""
        if self._available:
            idx = self._available.pop()
            detection = self._pool[idx]
            # Reuse existing object
            return detection._replace(type=type_, start=start, end=end, text=text)
        else:
            # Pool exhausted, create new
            return Detection(type_, start, end, text)
    
    def return_detection(self, detection: Detection):
        """Return detection to pool for reuse"""
        # Find index and mark as available
        try:
            idx = self._pool.index(detection)
            self._available.append(idx)
        except ValueError:
            pass  # Not from pool
```

## 5. Parser Optimization

### 5.1 Streaming JSON Parser
```python
class StreamingJSONParser:
    """Memory-efficient JSON parser for large documents"""
    
    def parse(self, data: Union[str, dict]) -> List[TextChunk]:
        if isinstance(data, str):
            # Parse incrementally
            return self._parse_json_string(data)
        else:
            # Direct object traversal
            return self._parse_json_object(data)
    
    def _parse_json_string(self, json_str: str) -> List[TextChunk]:
        """Stream-parse JSON string without loading entire structure"""
        import json
        
        # Use ijson for streaming if available, else fallback
        try:
            import ijson
            return self._stream_parse_ijson(json_str)
        except ImportError:
            # Fallback to standard parsing
            data = json.loads(json_str)
            return self._parse_json_object(data)
    
    def _extract_strings_iterative(self, obj: Any, path: List = None) -> List[TextChunk]:
        """Non-recursive string extraction to avoid stack overflow"""
        path = path or []
        chunks = []
        
        # Use explicit stack instead of recursion
        stack = [(obj, path.copy())]
        
        while stack:
            current_obj, current_path = stack.pop()
            
            if isinstance(current_obj, str):
                chunks.append({
                    'text': current_obj,
                    'path': current_path.copy(),
                    'type': 'json'
                })
            elif isinstance(current_obj, dict):
                for key, value in current_obj.items():
                    stack.append((value, current_path + [key]))
            elif isinstance(current_obj, list):
                for i, item in enumerate(current_obj):
                    stack.append((item, current_path + [i]))
        
        return chunks
```

### 5.2 Fast HTML Parser
```python
class FastHTMLParser:
    """Regex-based HTML parser optimized for text extraction"""
    
    # Pre-compiled patterns
    TEXT_PATTERN = re.compile(r'>([^<]+)<', re.MULTILINE)
    ATTR_PATTERN = re.compile(r'(?:alt|title|value|placeholder)="([^"]*)"', re.IGNORECASE)
    TAG_STRIP = re.compile(r'<[^>]+>')
    
    def parse(self, html: str) -> List[TextChunk]:
        """Fast HTML parsing using regex instead of DOM parser"""
        chunks = []
        
        # Extract text between tags
        for match in self.TEXT_PATTERN.finditer(html):
            text = match.group(1).strip()
            if text and len(text) > 1:  # Skip whitespace and single chars
                chunks.append({
                    'text': text,
                    'offset': match.start(1),
                    'type': 'html'
                })
        
        # Extract relevant attributes  
        for match in self.ATTR_PATTERN.finditer(html):
            attr_value = match.group(1).strip()
            if attr_value and len(attr_value) > 2:
                chunks.append({
                    'text': attr_value,
                    'offset': match.start(1),
                    'type': 'html_attr'
                })
        
        return chunks
    
    def reconstruct(self, original: str, chunks: List[TextChunk], 
                   replacements: List[str]) -> str:
        """Fast HTML reconstruction"""
        result = original
        
        # Sort by offset in reverse order
        chunk_pairs = list(zip(chunks, replacements))
        chunk_pairs.sort(key=lambda x: x[0]['offset'], reverse=True)
        
        # Apply replacements from right to left
        for chunk, replacement in chunk_pairs:
            start = chunk['offset']
            end = start + len(chunk['text'])
            result = result[:start] + replacement + result[end:]
        
        return result
```

## 6. Detection Merging Optimization

### 6.1 Efficient Conflict Resolution
```python
class FastDetectionMerger:
    def merge_and_deduplicate(self, detections: List[Detection]) -> List[Detection]:
        """Optimized O(n log n) merging algorithm"""
        if not detections:
            return []
        
        # Sort by start position, then by length (longer first)
        sorted_detections = sorted(
            detections, 
            key=lambda d: (d.start, d.start - d.end)  # Longer spans first
        )
        
        # Merge overlapping detections
        merged = []
        current = sorted_detections[0]
        
        for detection in sorted_detections[1:]:
            if detection.start < current.end:  # Overlap
                # Keep the longer detection or higher confidence type
                if self._is_better_detection(detection, current):
                    current = detection
                # Skip the worse detection
            else:
                # No overlap, add current and move to next
                merged.append(current)
                current = detection
        
        merged.append(current)
        return merged
    
    def _is_better_detection(self, new: Detection, current: Detection) -> bool:
        """Determine which detection is better to keep"""
        # Type priority (specific types beat generic)
        type_priority = {
            'EMAIL': 10, 'SSN': 10, 'CREDIT_CARD': 10,  # High confidence
            'PHONE': 8,                                   # Medium confidence  
            'PERSON': 5, 'ORGANIZATION': 5, 'LOCATION': 5 # NER types
        }
        
        new_priority = type_priority.get(new.type, 1)
        current_priority = type_priority.get(current.type, 1)
        
        if new_priority != current_priority:
            return new_priority > current_priority
        
        # Same priority, prefer longer span
        new_length = new.end - new.start
        current_length = current.end - current.start
        return new_length > current_length
```

## 7. System-Level Optimizations

### 7.1 Warm-up and Preloading
```python
class WarmupSanitizer(Sanitizer):
    """Sanitizer with warm-up to optimize first request performance"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self._warmed_up = False
    
    def warmup(self):
        """Warm up all components for optimal performance"""
        if self._warmed_up:
            return
        
        # Warm up regex compiler
        test_text = "john@example.com 555-1234 123-45-6789"
        self.detector.regex_detector.detect(test_text)
        
        # Warm up NER model (triggers lazy loading)
        if self.detector.ner_detector:
            self.detector.ner_detector.detect("John Doe works at Microsoft")
        
        # Warm up parsers
        test_json = {"email": "test@example.com"}
        self.sanitize(test_json)
        
        # Pre-JIT important methods
        self._warmup_jit()
        
        self._warmed_up = True
    
    def _warmup_jit(self):
        """Trigger JIT compilation for hot paths"""
        # Run key methods multiple times to trigger optimization
        sample_data = [
            "Contact john@example.com",
            {"user": "jane@company.com"},
            "<p>Email: admin@site.org</p>"
        ]
        
        for _ in range(10):  # Multiple runs for JIT
            for data in sample_data:
                self.sanitize(data)
```

### 7.2 Performance Monitoring
```python
class PerformanceMonitor:
    """Built-in performance monitoring and optimization alerts"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.thresholds = {
            'parse_time': 5,    # 5ms
            'detect_time': 80,  # 80ms  
            'mask_time': 5,     # 5ms
            'total_time': 100   # 100ms
        }
    
    def record_timing(self, operation: str, duration_ms: float):
        """Record timing for performance analysis"""
        self.metrics[operation].append(duration_ms)
        
        # Alert on threshold breach
        if duration_ms > self.thresholds.get(operation, float('inf')):
            self._alert_slow_operation(operation, duration_ms)
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics"""
        stats = {}
        for operation, timings in self.metrics.items():
            if timings:
                stats[operation] = {
                    'p50': np.percentile(timings, 50),
                    'p95': np.percentile(timings, 95),
                    'p99': np.percentile(timings, 99),
                    'mean': np.mean(timings),
                    'count': len(timings)
                }
        return stats
```

## 8. Compilation and Deployment Optimizations

### 8.1 PyInstaller Optimization
```python
# pyinstaller.spec
a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[('models/', 'models/')],  # Bundle NER model
    hiddenimports=['spacy.lang.en'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy.f2py', 'tkinter',  # Exclude unused modules
        'PIL', 'IPython', 'jupyter'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

# Optimize for size and startup
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='maskingengine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip debug symbols
    upx=True,    # Compress executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True
)
```

### 8.2 Docker Optimization
```dockerfile
# Multi-stage build for minimal image
FROM python:3.9-slim as builder

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and optimize model
RUN python -c "import spacy; spacy.download('en_core_web_sm')"

FROM python:3.9-slim as runtime

# Copy only necessary files
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY maskingengine/ /app/maskingengine/
WORKDIR /app

# Optimize Python startup
ENV PYTHONOPTIMIZE=2
ENV PYTHONDONTWRITEBYTECODE=1

# Pre-warm the application
RUN python -c "from maskingengine import Sanitizer; s = Sanitizer(); s.warmup()"

EXPOSE 8000
CMD ["python", "-m", "maskingengine.api"]
```

## 9. Performance Testing Framework

### 9.1 Benchmark Suite
```python
class PerformanceBenchmark:
    """Comprehensive performance testing"""
    
    def run_latency_benchmarks(self):
        """Test latency across different document sizes"""
        sanitizer = Sanitizer()
        sanitizer.warmup()  # Warm start
        
        test_cases = [
            ('1KB', generate_text(1024)),
            ('10KB', generate_text(10240)),
            ('100KB', generate_text(102400)),
        ]
        
        results = {}
        for name, text in test_cases:
            timings = []
            for _ in range(100):  # 100 runs
                start = time.perf_counter()
                sanitizer.sanitize(text)
                end = time.perf_counter()
                timings.append((end - start) * 1000)  # ms
            
            results[name] = {
                'p50': np.percentile(timings, 50),
                'p95': np.percentile(timings, 95),
                'p99': np.percentile(timings, 99)
            }
        
        return results
    
    def run_throughput_benchmark(self):
        """Test concurrent throughput"""
        sanitizer = Sanitizer()
        documents = [generate_mixed_pii_doc() for _ in range(1000)]
        
        start = time.time()
        
        # Process concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(sanitizer.sanitize, documents))
        
        end = time.time()
        
        total_time = end - start
        throughput = len(documents) / total_time
        
        return {
            'documents': len(documents),
            'total_time': total_time,
            'throughput': throughput,
            'avg_per_doc': total_time / len(documents) * 1000  # ms
        }
```

This performance optimization strategy ensures the MaskingEngine meets its <100ms latency target while maintaining accuracy and simplicity.