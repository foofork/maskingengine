"""Test placeholder stability across streaming chunks."""

import pytest
from maskingengine.pipeline import StreamingMaskingSession, StreamingTextProcessor, StreamingChunk
from maskingengine.config import Config


class TestPlaceholderStability:
    """Test that placeholders remain consistent across streaming chunks."""
    
    def test_consistent_placeholders_same_pii(self):
        """Test that identical PII gets the same placeholder across chunks."""
        config = Config(regex_only=True)
        session = StreamingMaskingSession(config, session_id="test_session")
        
        # First chunk with an email
        chunk1 = StreamingChunk(
            chunk_id=0,
            content="Contact john@example.com for details",
            start_offset=0,
            end_offset=35
        )
        
        result1 = session.process_chunk(chunk1)
        
        # Second chunk with the same email
        chunk2 = StreamingChunk(
            chunk_id=1,
            content="Email john@example.com again",
            start_offset=36,
            end_offset=64
        )
        
        result2 = session.process_chunk(chunk2)
        
        # Extract placeholders for john@example.com from both chunks
        email_placeholders = []
        
        for result in [result1, result2]:
            for detection in result.detections:
                if detection['original_value'] == 'john@example.com':
                    email_placeholders.append(detection['placeholder'])
        
        # Should have found the email in both chunks with the same placeholder
        # Note: There might be multiple detections per chunk, so we check unique placeholders
        unique_placeholders = list(set(email_placeholders))
        assert len(unique_placeholders) == 1, f"Expected 1 unique placeholder, got {len(unique_placeholders)}: {unique_placeholders}"
        assert unique_placeholders[0].startswith('<<EMAIL_')
        
        # Verify both chunks detected the same email
        assert len(email_placeholders) >= 2, f"Expected at least 2 detections, got {len(email_placeholders)}"
    
    def test_different_placeholders_different_pii(self):
        """Test that different PII gets different placeholders."""
        config = Config(regex_only=True)
        session = StreamingMaskingSession(config, session_id="test_session")
        
        chunk = StreamingChunk(
            chunk_id=0,
            content="Email john@example.com or jane@company.com",
            start_offset=0,
            end_offset=42
        )
        
        result = session.process_chunk(chunk)
        
        # Should detect two different emails with different placeholders
        email_detections = [d for d in result.detections if d['type'] == 'EMAIL']
        assert len(email_detections) == 2
        
        placeholders = [d['placeholder'] for d in email_detections]
        assert placeholders[0] != placeholders[1]
        assert all(p.startswith('<<EMAIL_') for p in placeholders)
    
    def test_cross_chunk_pii_consistency(self):
        """Test PII consistency when the same entity appears in multiple chunks."""
        config = Config(regex_only=True)
        session = StreamingMaskingSession(config, session_id="test_cross_chunk")
        
        # Process multiple chunks with repeating PII
        test_data = [
            "Call 555-123-4567 for support",
            "Number 555-123-4567 is main line",
            "Reach us at 555-123-4567 anytime"
        ]
        
        phone_placeholders = []
        
        for i, content in enumerate(test_data):
            chunk = StreamingChunk(
                chunk_id=i,
                content=content,
                start_offset=i * 50,
                end_offset=(i + 1) * 50
            )
            
            result = session.process_chunk(chunk)
            
            # Find phone number detections
            for detection in result.detections:
                if detection['original_value'] == '555-123-4567':
                    phone_placeholders.append(detection['placeholder'])
        
        # All occurrences should have the same placeholder
        unique_placeholders = list(set(phone_placeholders))
        assert len(unique_placeholders) == 1, f"Expected 1 unique placeholder, got {len(unique_placeholders)}: {unique_placeholders}"
        assert unique_placeholders[0].startswith('<<PHONE_')
        assert len(phone_placeholders) >= 3, f"Expected at least 3 detections, got {len(phone_placeholders)}"
    
    def test_counter_increments_for_different_entities(self):
        """Test that counters increment properly for different entities of the same type."""
        config = Config(regex_only=True)
        session = StreamingMaskingSession(config, session_id="test_counters")
        
        chunk = StreamingChunk(
            chunk_id=0,
            content="Email alice@company.com and bob@company.com and charlie@company.com",
            start_offset=0,
            end_offset=70
        )
        
        result = session.process_chunk(chunk)
        
        # Should detect three different emails
        email_detections = [d for d in result.detections if d['type'] == 'EMAIL']
        assert len(email_detections) == 3
        
        # Extract counter numbers from placeholders
        counters = []
        for detection in email_detections:
            placeholder = detection['placeholder']
            # Format: <<EMAIL_HASH_COUNTER>>
            parts = placeholder[2:-2].split('_')
            counter = int(parts[-1])
            counters.append(counter)
        
        # Counters should be sequential
        counters.sort()
        assert counters == [1, 2, 3]
    
    def test_session_isolation(self):
        """Test that different sessions maintain separate state."""
        config = Config(regex_only=True)
        
        # Create two different sessions
        session1 = StreamingMaskingSession(config, session_id="session_1")
        session2 = StreamingMaskingSession(config, session_id="session_2")
        
        content = "Contact john@example.com"
        
        chunk1 = StreamingChunk(
            chunk_id=0,
            content=content,
            start_offset=0,
            end_offset=len(content)
        )
        
        chunk2 = StreamingChunk(
            chunk_id=0,
            content=content,
            start_offset=0,
            end_offset=len(content)
        )
        
        result1 = session1.process_chunk(chunk1)
        result2 = session2.process_chunk(chunk2)
        
        # Extract placeholders
        placeholder1 = result1.detections[0]['placeholder']
        placeholder2 = result2.detections[0]['placeholder']
        
        # Both sessions should generate valid placeholders
        assert placeholder1.startswith('<<EMAIL_')
        assert placeholder2.startswith('<<EMAIL_')
        
        # Sessions should maintain their own state
        assert session1.session_id != session2.session_id
        assert len(session1.seen_pii_hashes) >= 1  # Session 1 has processed PII
        assert len(session2.seen_pii_hashes) >= 1  # Session 2 has processed PII
    
    def test_session_statistics(self):
        """Test that session statistics are correctly maintained."""
        config = Config(regex_only=True)
        session = StreamingMaskingSession(config, session_id="test_stats")
        
        # Process multiple chunks
        chunks = [
            "Email: john@example.com",
            "Phone: 555-123-4567", 
            "Another email: jane@company.com",
            "Same phone: 555-123-4567"  # Repeat
        ]
        
        for i, content in enumerate(chunks):
            chunk = StreamingChunk(
                chunk_id=i,
                content=content,
                start_offset=i * 30,
                end_offset=(i + 1) * 30
            )
            session.process_chunk(chunk)
        
        stats = session.get_session_stats()
        
        # Verify statistics
        assert stats['session_id'] == "test_stats"
        assert stats['total_detections'] >= 4  # At least 4 detections
        assert stats['unique_pii_seen'] >= 3  # At least 3 unique PII items
        assert 'EMAIL' in stats['pii_types_detected']
        assert 'PHONE' in stats['pii_types_detected']
        assert stats['placeholder_counters']['EMAIL'] >= 2  # At least 2 email placeholders
        assert 'PHONE' in stats['placeholder_counters']  # At least some phone detection
    
    def test_streaming_text_processor(self):
        """Test the streaming text processor utility."""
        text = "This is a test email john@example.com and phone 555-123-4567 in a long text."
        
        # Test chunking
        chunks = list(StreamingTextProcessor.from_string(text, chunk_size=20))
        
        # Should break into multiple chunks
        assert len(chunks) > 1
        
        # Reassemble should match original
        reassembled = ''.join(chunks)
        assert reassembled == text
    
    def test_overlap_handling(self):
        """Test that overlapping chunks handle PII correctly."""
        config = Config(regex_only=True)
        session = StreamingMaskingSession(config, session_id="test_overlap")
        
        # Create chunks where PII might be split across boundaries
        full_text = "Please contact our support at support@company.com for assistance"
        
        # Process as stream
        results = list(session.process_stream(
            StreamingTextProcessor.from_string(full_text, chunk_size=20)
        ))
        
        # Combine results
        combined_content = ''.join(result.masked_content for result in results)
        
        # Should contain the email placeholder
        assert '<<EMAIL_' in combined_content
        assert 'support@company.com' not in combined_content