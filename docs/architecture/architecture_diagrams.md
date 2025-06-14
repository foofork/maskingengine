# Architecture Diagrams - Minimal PII Sanitizer

## 1. High-Level Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Input     │     │   Config    │     │   Output    │
│ text/JSON/  │────▶│  Patterns   │────▶│  Sanitized  │
│    HTML     │     │   Hashes    │     │    Data     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  Sanitizer Pipeline                  │
│                                                     │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────┐ │
│  │ Parser  │─▶│ Detector │─▶│  Masker  │─▶│ Out │ │
│  └─────────┘  └──────────┘  └──────────┘  └─────┘ │
└─────────────────────────────────────────────────────┘
```

## 2. Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Sanitizer                            │
│                    (Main Orchestrator)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. sanitize(input) ──┐                                    │
│                       ▼                                     │
│  ┌──────────────────────────────────┐                      │
│  │         Parser.parse()           │                      │
│  │  • Auto-detect format            │                      │
│  │  • Extract text chunks           │                      │
│  │  • Track positions               │                      │
│  └────────────┬─────────────────────┘                      │
│               │ chunks[]                                    │
│               ▼                                             │
│  ┌──────────────────────────────────┐                      │
│  │      Detector.detect_all()       │                      │
│  │  • RegexDetector.detect()        │                      │
│  │  • NERDetector.detect()          │                      │
│  │  • Deduplicate results           │                      │
│  └────────────┬─────────────────────┘                      │
│               │ detections[]                                │
│               ▼                                             │
│  ┌──────────────────────────────────┐                      │
│  │        Masker.mask()             │                      │
│  │  • Sort detections reverse       │                      │
│  │  • Apply <<TYPE_HASH>>           │                      │
│  │  • Return masked text            │                      │
│  └────────────┬─────────────────────┘                      │
│               │ masked_text                                 │
│               ▼                                             │
│  ┌──────────────────────────────────┐                      │
│  │    Reconstruct Output            │                      │
│  │  • Text: return as-is            │                      │
│  │  • JSON: rebuild structure       │                      │
│  │  • HTML: preserve tags           │                      │
│  └──────────────────────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 3. Module Dependencies

```
┌─────────────┐
│  sanitizer  │ ◄── Main entry point
└──────┬──────┘
       │ imports
       ▼
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   config    │   parsers   │  detectors  │   masker    │
└─────────────┴──────┬──────┴──────┬──────┴─────────────┘
                     │              │
                     │              │ imports
                     │              ▼
                     │         ┌─────────────┐
                     │         │   config    │
                     │         └─────────────┘
                     │
                     └──────── No circular dependencies
```

## 4. Parser Module Flow

```
Parser.parse(input)
       │
       ├─── isinstance(dict)? ──Yes──▶ JSONParser.parse()
       │                                      │
       │                                      ▼
       │                               Extract all string
       │                               values with paths
       │
       ├─── '<' in text[:100]? ──Yes──▶ HTMLParser.parse()
       │                                      │
       │                                      ▼
       │                                Use regex to find
       │                                text between tags
       │
       └─── Default ──────────────────▶ TextParser.parse()
                                             │
                                             ▼
                                      Return single chunk
                                      with full text
```

## 5. Detector Pipeline

```
Detector.detect_all(text)
        │
        ├──── Phase 1: Regex Detection (Fast Path)
        │     │
        │     ├─▶ EMAIL pattern     ─┐
        │     ├─▶ PHONE pattern     ─┤
        │     ├─▶ SSN pattern       ─┼─▶ Collect matches
        │     └─▶ CREDIT_CARD pattern┘
        │
        ├──── Phase 2: NER Detection (If Enabled)
        │     │
        │     ├─▶ Load spaCy model (lazy)
        │     ├─▶ Process text
        │     └─▶ Extract PERSON, ORG, GPE entities
        │
        └──── Phase 3: Deduplication
              │
              ├─▶ Sort by start position
              ├─▶ Remove overlapping detections
              └─▶ Return merged list
```

## 6. Masking Process

```
text: "John Doe's email is john@example.com"
      └─┬─┘ └─┬─┘           └────┬────┘
        │     │                  │
detections: [(PERSON,0,8), (PERSON,9,12), (EMAIL,20,36)]
        │
        ▼
Sort reverse by position: [(EMAIL,20,36), (PERSON,9,12), (PERSON,0,8)]
        │
        ▼
Apply masks (right to left):
1. "John Doe's email is <<EMAIL_7A9B2C>>"
2. "John Doe's email is <<EMAIL_7A9B2C>>"  (9,12 inside previous)
3. "<<PERSON_9E4C6A>>'s email is <<EMAIL_7A9B2C>>"
```

## 7. API Request Flow

```
┌────────┐      ┌─────────────┐      ┌────────────┐
│ Client │─────▶│  FastAPI    │─────▶│ Sanitizer  │
└────────┘      │  Endpoint   │      └────────────┘
                └─────────────┘             │
                       ▲                    │
                       │                    ▼
                ┌─────────────┐      ┌────────────┐
                │   Response   │◄─────│   Result   │
                │   + timing   │      └────────────┘
                └─────────────┘

Request:  {"content": "...", "format": "auto"}
Response: {"sanitized": "...", "processing_time_ms": 45}
```

## 8. CLI Data Flow

```
┌─────────┐     ┌─────────┐     ┌────────────┐     ┌─────────┐
│  stdin  │────▶│   CLI   │────▶│ Sanitizer  │────▶│ stdout  │
└─────────┘     │  Args   │     └────────────┘     └─────────┘
     or         └─────────┘
┌─────────┐          │
│  File   │──────────┘
└─────────┘

Examples:
$ echo "text" | maskingengine
$ maskingengine -i input.txt -o output.txt
$ maskingengine -f json < data.json
```

## 9. Performance Critical Path

```
                 ┌─────────────────┐
                 │ Input (1-100KB) │
                 └────────┬────────┘
                          │ <1ms
                 ┌────────▼────────┐
                 │ Format Detection│
                 └────────┬────────┘
                          │ <2ms
                 ┌────────▼────────┐
                 │ Text Extraction │
                 └────────┬────────┘
                          │ 
     ┌────────────────────┴────────────────────┐
     │                                         │
     ▼ 5-20ms                                  ▼ 30-60ms
┌─────────────┐                          ┌─────────────┐
│Regex Detect │                          │ NER Detect  │
└──────┬──────┘                          └──────┬──────┘
       │                                         │
       └────────────────┬────────────────────────┘
                        │ <1ms
               ┌────────▼────────┐
               │ Deduplication   │
               └────────┬────────┘
                        │ <5ms
               ┌────────▼────────┐
               │ Apply Masks     │
               └────────┬────────┘
                        │ <2ms
               ┌────────▼────────┐
               │ Reconstruct     │
               └────────┬────────┘
                        │
                 Total: <100ms
```

## 10. Memory Layout

```
┌─────────────────────────────────────┐
│         Sanitizer Instance          │
├─────────────────────────────────────┤
│ config: Config                      │ ← ~1KB
│   - PATTERNS (compiled regex)       │ ← ~10KB
│   - TYPE_HASHES                     │ ← ~100B
├─────────────────────────────────────┤
│ detector: Detector                  │
│   - regex_detector                  │ ← ~10KB
│   - ner_detector (lazy)            │ ← ~40MB when loaded
├─────────────────────────────────────┤
│ masker: Masker                     │ ← ~1KB
│   - type_hashes reference          │
└─────────────────────────────────────┘

Total Memory: ~50MB (with NER model loaded)
             ~20KB (without NER model)
```

## 11. Error Handling Flow

```
sanitize(input)
      │
      ├──Try─────────────────┐
      │                      ▼
      │              Main Pipeline
      │                      │
      │                      ├─ Success ──▶ Return result
      │                      │
      │                      └─ Exception ─┐
      │                                    │
      └──Except──────────────────────────┐ │
                                         ▼ ▼
                                   Handle Errors
                                         │
         ┌───────────────┬───────────────┼───────────────┬──────────────┐
         ▼               ▼               ▼               ▼              ▼
    ParseError      NER Error      Timeout         OOM          Unknown
         │               │               │               │              │
         ▼               ▼               ▼               ▼              ▼
    Use text        Use regex       Return         Reject         Log & 
    parser          only           partial         input         continue
```

## 12. Configuration Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Defaults   │────▶│   Config()   │────▶│  Components  │
└─────────────┘     └──────────────┘     └──────────────┘
                           │
                           ├─▶ PATTERNS ────▶ RegexDetector
                           ├─▶ TYPE_HASHES ─▶ Masker
                           ├─▶ NER_ENABLED ─▶ Detector
                           └─▶ NER_MODEL ───▶ NERDetector
```