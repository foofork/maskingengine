"""Streaming masking pipeline for processing large inputs in chunks."""

from typing import Dict, List, Optional, Iterator, Tuple, Any
import hashlib
from dataclasses import dataclass

from ..sanitizer import Sanitizer
from ..config import Config


@dataclass
class StreamingChunk:
    """Represents a chunk of text with its position in the stream."""
    chunk_id: int
    content: str
    start_offset: int
    end_offset: int
    is_final: bool = False


@dataclass
class StreamingResult:
    """Result of processing a chunk with stable placeholders."""
    chunk_id: int
    masked_content: str
    detections: List[Dict[str, Any]]
    placeholder_count: int
    start_offset: int
    end_offset: int


class StreamingMaskingSession:
    """Manages streaming PII masking with consistent placeholder generation."""
    
    def __init__(self, config: Optional[Config] = None, session_id: Optional[str] = None):
        """Initialize streaming session.
        
        Args:
            config: MaskingEngine configuration
            session_id: Optional session ID for consistent placeholders
        """
        self.config = config or Config()
        self.session_id = session_id or self._generate_session_id()
        self.sanitizer = Sanitizer(self.config)
        
        # Streaming state
        self.chunk_counter = 0
        self.global_placeholder_counters: Dict[str, int] = {}
        self.seen_pii_hashes: Dict[str, str] = {}  # Maps PII content hash to placeholder
        self.total_detections = 0
        
        # Buffering for cross-chunk patterns
        self.overlap_buffer = ""
        self.overlap_size = 100  # Characters to overlap between chunks
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import time
        timestamp = str(int(time.time() * 1000))
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _get_pii_hash(self, content: str, pii_type: str) -> str:
        """Generate a consistent hash for PII content."""
        combined = f"{self.session_id}:{pii_type}:{content}"
        return hashlib.md5(combined.encode()).hexdigest()[:6]
    
    def _generate_consistent_placeholder(self, content: str, pii_type: str) -> str:
        """Generate consistent placeholder for the same PII across chunks."""
        # Check if we've seen this exact PII content before
        content_hash = self._get_pii_hash(content, pii_type)
        
        if content_hash in self.seen_pii_hashes:
            return self.seen_pii_hashes[content_hash]
        
        # Get type hash from config
        type_hash = self.config.TYPE_HASHES.get(pii_type, 'UNKNOWN')
        
        # Increment counter for this type
        if pii_type not in self.global_placeholder_counters:
            self.global_placeholder_counters[pii_type] = 0
        self.global_placeholder_counters[pii_type] += 1
        
        # Generate placeholder
        placeholder = f"<<{pii_type}_{type_hash}_{self.global_placeholder_counters[pii_type]}>>"
        
        # Cache this mapping
        self.seen_pii_hashes[content_hash] = placeholder
        
        return placeholder
    
    def _preprocess_chunk(self, content: str, is_first_chunk: bool) -> str:
        """Preprocess chunk to handle overlapping patterns."""
        if is_first_chunk:
            self.overlap_buffer = ""
            return content
        
        # Prepend overlap buffer from previous chunk
        combined_content = self.overlap_buffer + content
        return combined_content
    
    def _postprocess_chunk(self, masked_content: str, original_content: str, 
                          is_first_chunk: bool, is_final_chunk: bool) -> Tuple[str, str]:
        """Postprocess chunk and update overlap buffer."""
        if is_final_chunk:
            # No need to handle overlap for final chunk
            return masked_content, ""
        
        # Extract overlap for next chunk
        if len(original_content) > self.overlap_size:
            overlap_start = len(original_content) - self.overlap_size
            self.overlap_buffer = original_content[overlap_start:]
            
            # Trim the processed content to avoid duplication
            if not is_first_chunk:
                # Remove the overlap we added at the beginning
                if len(masked_content) > self.overlap_size:
                    masked_content = masked_content[self.overlap_size:]
        else:
            self.overlap_buffer = original_content
        
        return masked_content, self.overlap_buffer
    
    def process_chunk(self, chunk: StreamingChunk) -> StreamingResult:
        """Process a single chunk with consistent placeholders.
        
        Args:
            chunk: StreamingChunk to process
            
        Returns:
            StreamingResult with masked content and metadata
        """
        is_first_chunk = chunk.chunk_id == 0
        
        # Preprocess chunk with overlap handling
        processed_content = self._preprocess_chunk(chunk.content, is_first_chunk)
        
        # Perform PII detection and masking
        masked_content, mask_map = self.sanitizer.sanitize(processed_content)
        
        # Replace placeholders with consistent ones across the session
        detections = []
        placeholder_count = 0
        
        # Extract detections and replace with consistent placeholders
        for placeholder, original_value in mask_map.items():
            # Extract PII type from placeholder
            if placeholder.startswith('<<') and placeholder.endswith('>>'):
                parts = placeholder[2:-2].split('_')
                if len(parts) >= 2:
                    pii_type = parts[0]
                    
                    # Generate consistent placeholder
                    consistent_placeholder = self._generate_consistent_placeholder(
                        original_value, pii_type
                    )
                    
                    # Replace in masked content
                    masked_content = masked_content.replace(placeholder, consistent_placeholder)
                    
                    # Record detection
                    detections.append({
                        'type': pii_type,
                        'original_value': original_value,
                        'placeholder': consistent_placeholder,
                        'chunk_id': chunk.chunk_id
                    })
                    placeholder_count += 1
        
        # Postprocess chunk for overlap
        final_content, next_overlap = self._postprocess_chunk(
            masked_content, chunk.content, is_first_chunk, chunk.is_final
        )
        
        self.total_detections += placeholder_count
        
        return StreamingResult(
            chunk_id=chunk.chunk_id,
            masked_content=final_content,
            detections=detections,
            placeholder_count=placeholder_count,
            start_offset=chunk.start_offset,
            end_offset=chunk.end_offset
        )
    
    def process_stream(self, content_iterator: Iterator[str], 
                      chunk_size: int = 4096) -> Iterator[StreamingResult]:
        """Process a stream of content in chunks.
        
        Args:
            content_iterator: Iterator yielding content strings
            chunk_size: Size of chunks to process
            
        Yields:
            StreamingResult for each processed chunk
        """
        buffer = ""
        current_offset = 0
        chunk_id = 0
        
        for content in content_iterator:
            buffer += content
            
            # Process complete chunks
            while len(buffer) >= chunk_size:
                chunk_content = buffer[:chunk_size]
                buffer = buffer[chunk_size:]
                
                chunk = StreamingChunk(
                    chunk_id=chunk_id,
                    content=chunk_content,
                    start_offset=current_offset,
                    end_offset=current_offset + len(chunk_content)
                )
                
                result = self.process_chunk(chunk)
                yield result
                
                current_offset += len(chunk_content)
                chunk_id += 1
        
        # Process final chunk if any content remains
        if buffer:
            chunk = StreamingChunk(
                chunk_id=chunk_id,
                content=buffer,
                start_offset=current_offset,
                end_offset=current_offset + len(buffer),
                is_final=True
            )
            
            result = self.process_chunk(chunk)
            yield result
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current streaming session.
        
        Returns:
            Dictionary with session statistics
        """
        return {
            'session_id': self.session_id,
            'chunks_processed': self.chunk_counter,
            'total_detections': self.total_detections,
            'unique_pii_seen': len(self.seen_pii_hashes),
            'placeholder_counters': self.global_placeholder_counters.copy(),
            'pii_types_detected': list(self.global_placeholder_counters.keys())
        }
    
    def reset_session(self) -> None:
        """Reset the session state for reuse."""
        self.chunk_counter = 0
        self.global_placeholder_counters.clear()
        self.seen_pii_hashes.clear()
        self.total_detections = 0
        self.overlap_buffer = ""
        self.session_id = self._generate_session_id()


class StreamingTextProcessor:
    """Helper class for processing text streams from various sources."""
    
    @staticmethod
    def from_string(text: str, chunk_size: int = 4096) -> Iterator[str]:
        """Create iterator from a string.
        
        Args:
            text: Input text to chunk
            chunk_size: Size of each chunk
            
        Yields:
            String chunks
        """
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]
    
    @staticmethod
    def from_file(file_path: str, chunk_size: int = 4096) -> Iterator[str]:
        """Create iterator from a file.
        
        Args:
            file_path: Path to input file
            chunk_size: Size of each chunk
            
        Yields:
            String chunks from file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    def from_stdin(chunk_size: int = 4096) -> Iterator[str]:
        """Create iterator from stdin.
        
        Args:
            chunk_size: Size of each chunk
            
        Yields:
            String chunks from stdin
        """
        import sys
        while True:
            chunk = sys.stdin.read(chunk_size)
            if not chunk:
                break
            yield chunk