# Phase 2: Pseudocode Design - Local-First PII Sanitizer

## 1. Core Detection Engine

### 1.1 Main Sanitizer Class
```pseudocode
class Sanitizer:
    def __init__(config):
        self.regex_detector = RegexDetector(config.patterns)
        self.ner_detector = NERDetector(config.model_path)
        self.masker = Masker(config.mask_format)
        self.format_handlers = {
            'text': TextHandler(),
            'json': JSONHandler(),
            'html': HTMLHandler()
        }
    
    def sanitize(input_data, format='auto'):
        # Auto-detect format if needed
        if format == 'auto':
            format = detect_format(input_data)
        
        # Get appropriate handler
        handler = self.format_handlers[format]
        
        # Parse input into processable chunks
        chunks = handler.parse(input_data)
        
        # Process each chunk
        results = []
        for chunk in chunks:
            # Run detection pipeline
            detections = self.detect_pii(chunk.text)
            
            # Apply masking
            masked_text = self.apply_masks(chunk.text, detections)
            
            # Reconstruct with original format
            results.append(handler.reconstruct(chunk, masked_text))
        
        # Combine results
        return handler.combine(results)
    
    def detect_pii(text):
        # Run both detectors in parallel
        regex_results = self.regex_detector.detect(text)
        ner_results = self.ner_detector.detect(text)
        
        # Merge and deduplicate results
        all_detections = merge_detections(regex_results, ner_results)
        
        # Resolve conflicts (overlapping detections)
        resolved = resolve_conflicts(all_detections)
        
        return resolved
```

### 1.2 Regex Detection Algorithm
```pseudocode
class RegexDetector:
    def __init__(patterns_config):
        self.patterns = load_patterns(patterns_config)
        self.compiled_patterns = compile_patterns(self.patterns)
    
    def detect(text):
        detections = []
        
        for pattern_name, regex in self.compiled_patterns:
            matches = regex.find_all(text)
            
            for match in matches:
                detection = Detection(
                    type=pattern_name,
                    start=match.start,
                    end=match.end,
                    text=match.text,
                    confidence=pattern.confidence,
                    method='regex'
                )
                detections.append(detection)
        
        return detections

# Pattern definitions
PATTERNS = {
    'email': {
        'regex': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'confidence': 0.95
    },
    'phone_us': {
        'regex': r'(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
        'confidence': 0.85
    },
    'ssn': {
        'regex': r'\b\d{3}-\d{2}-\d{4}\b',
        'confidence': 0.90
    },
    'credit_card': {
        'regex': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'confidence': 0.80,
        'validator': luhn_check
    }
}
```

### 1.3 NER Detection Algorithm
```pseudocode
class NERDetector:
    def __init__(model_path):
        self.model = load_lightweight_ner_model(model_path)
        self.entity_types = ['PERSON', 'ORGANIZATION', 'LOCATION', 'EMAIL', 'PHONE']
    
    def detect(text):
        # Tokenize text
        tokens = tokenize(text)
        
        # Run NER model
        predictions = self.model.predict(tokens)
        
        # Convert predictions to detections
        detections = []
        current_entity = None
        
        for i, (token, label, confidence) in enumerate(predictions):
            if label != 'O':  # Not outside entity
                if current_entity is None:
                    current_entity = {
                        'type': label,
                        'tokens': [token],
                        'start': token.start,
                        'confidence': confidence
                    }
                elif current_entity['type'] == label:
                    current_entity['tokens'].append(token)
                else:
                    # End current entity, start new one
                    detections.append(create_detection(current_entity))
                    current_entity = {
                        'type': label,
                        'tokens': [token],
                        'start': token.start,
                        'confidence': confidence
                    }
            else:
                if current_entity:
                    detections.append(create_detection(current_entity))
                    current_entity = None
        
        return detections
```

## 2. Format Handlers

### 2.1 JSON Handler
```pseudocode
class JSONHandler:
    def parse(json_input):
        # Parse JSON structure
        data = json.parse(json_input)
        
        # Extract text chunks with paths
        chunks = []
        extract_chunks(data, chunks, path=[])
        
        return chunks
    
    def extract_chunks(obj, chunks, path):
        if isinstance(obj, str):
            chunks.append(TextChunk(
                text=obj,
                path=path.copy(),
                original=obj
            ))
        elif isinstance(obj, dict):
            for key, value in obj.items():
                extract_chunks(value, chunks, path + [key])
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_chunks(item, chunks, path + [i])
    
    def reconstruct(chunk, masked_text):
        # Return path and new value
        return {
            'path': chunk.path,
            'value': masked_text
        }
    
    def combine(results):
        # Rebuild JSON with masked values
        output = deep_copy(self.original_data)
        
        for result in results:
            set_by_path(output, result['path'], result['value'])
        
        return json.stringify(output)
```

### 2.2 HTML Handler
```pseudocode
class HTMLHandler:
    def parse(html_input):
        # Parse HTML safely
        doc = html_parser.parse(html_input)
        
        # Extract text nodes
        chunks = []
        for node in doc.traverse():
            if node.type == 'text':
                chunks.append(TextChunk(
                    text=node.value,
                    node=node,
                    original=node.value
                ))
            elif node.type == 'attribute':
                # Check specific attributes that might contain PII
                if node.name in ['alt', 'title', 'value', 'placeholder']:
                    chunks.append(TextChunk(
                        text=node.value,
                        node=node,
                        original=node.value,
                        is_attribute=True
                    ))
        
        return chunks
    
    def reconstruct(chunk, masked_text):
        # Update node value
        if chunk.is_attribute:
            chunk.node.set_attribute_value(masked_text)
        else:
            chunk.node.set_text_value(masked_text)
        
        return chunk.node
    
    def combine(results):
        # Return serialized HTML
        return self.doc.serialize()
```

## 3. Masking Logic

### 3.1 Masking Algorithm
```pseudocode
class Masker:
    def __init__(mask_format):
        self.format = mask_format
        self.token_map = {}  # For reversible masking
    
    def apply_masks(text, detections):
        # Sort detections by position (reverse order)
        sorted_detections = sort_by_position_desc(detections)
        
        # Apply masks from end to beginning
        masked_text = text
        for detection in sorted_detections:
            mask = generate_mask(detection)
            
            # Store mapping if reversible
            if self.format.reversible:
                token = generate_token()
                self.token_map[token] = detection.text
                mask = f"[{detection.type}:{token}]"
            
            # Replace text with mask
            masked_text = (
                masked_text[:detection.start] +
                mask +
                masked_text[detection.end:]
            )
        
        return masked_text
    
    def generate_mask(detection):
        if self.format.type_aware:
            return f"[{detection.type.upper()}]"
        elif self.format.length_preserving:
            return '*' * len(detection.text)
        else:
            return '[MASKED]'
```

## 4. Performance Optimizations

### 4.1 Parallel Processing
```pseudocode
def process_batch(documents):
    # Use thread pool for I/O bound operations
    with ThreadPool(workers=cpu_count()) as pool:
        # Parse all documents in parallel
        parsed = pool.map(parse_document, documents)
        
        # Detect PII in parallel
        detections = pool.map(detect_pii_optimized, parsed)
        
        # Apply masks in parallel
        results = pool.map(apply_masks_batch, zip(parsed, detections))
    
    return results

def detect_pii_optimized(text):
    # Run regex and NER in parallel
    with concurrent.futures:
        regex_future = executor.submit(regex_detect, text)
        ner_future = executor.submit(ner_detect, text)
        
        regex_results = regex_future.result()
        ner_results = ner_future.result()
    
    return merge_results(regex_results, ner_results)
```

### 4.2 Caching Strategy
```pseudocode
class DetectionCache:
    def __init__(max_size=1000):
        self.cache = LRUCache(max_size)
        self.hash_func = xxhash  # Fast non-crypto hash
    
    def get_or_compute(text, detector_func):
        # Generate cache key
        key = self.hash_func(text)
        
        # Check cache
        if key in self.cache:
            return self.cache[key]
        
        # Compute and cache
        result = detector_func(text)
        self.cache[key] = result
        
        return result
```

## 5. Error Handling

### 5.1 Graceful Degradation
```pseudocode
def safe_detect(text, timeout=0.1):
    try:
        # Set timeout for detection
        with timeout_context(timeout):
            detections = detect_pii(text)
            return detections
    except TimeoutError:
        # Fall back to regex only
        log.warning("NER timeout, using regex only")
        return regex_detector.detect(text)
    except Exception as e:
        # Log error and return empty
        log.error(f"Detection failed: {e}")
        return []

def safe_parse(input_data, format):
    try:
        return format_handlers[format].parse(input_data)
    except ParseError:
        # Try plain text fallback
        return TextHandler().parse(str(input_data))
    except Exception as e:
        # Return as single chunk
        return [TextChunk(text=str(input_data))]
```

## 6. TDD Anchors

### 6.1 Test Categories
```pseudocode
# Unit Tests
- test_regex_patterns_basic()
- test_regex_patterns_edge_cases()
- test_ner_detection_accuracy()
- test_masking_formats()
- test_format_parsers()

# Integration Tests  
- test_end_to_end_text_sanitization()
- test_json_structure_preservation()
- test_html_markup_preservation()
- test_detection_merging()
- test_conflict_resolution()

# Performance Tests
- test_latency_under_100ms()
- test_memory_usage()
- test_batch_processing()
- test_large_document_handling()

# Edge Case Tests
- test_invalid_input_handling()
- test_encoding_issues()
- test_partial_pii_detection()
- test_international_formats()
```

### 6.2 Test Data Generation
```pseudocode
def generate_test_data():
    test_cases = []
    
    # Basic PII patterns
    for pii_type in PII_TYPES:
        test_cases.extend(generate_valid_cases(pii_type, count=10))
        test_cases.extend(generate_invalid_cases(pii_type, count=5))
        test_cases.extend(generate_edge_cases(pii_type, count=5))
    
    # Format-specific cases
    test_cases.extend(generate_json_test_cases())
    test_cases.extend(generate_html_test_cases())
    
    # Performance test data
    test_cases.extend(generate_large_documents())
    
    return test_cases
```