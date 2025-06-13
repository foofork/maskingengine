"""NER-based PII detection using transformer models."""

import logging
from typing import List, Tuple, Optional
from pathlib import Path
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    pipeline,
    Pipeline
)


class NERDetector:
    """Detects unstructured PII using NER transformer models."""
    
    MODEL_NAME = "distilbert-base-multilingual-cased"
    DETECTED_ENTITIES = ["PER", "PERSON", "LOC", "LOCATION", "ORG", "ORGANIZATION"]
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize NER detector.
        
        Args:
            model_path: Optional path to local model. If not provided, downloads from HuggingFace.
            device: Device to run model on ('cpu', 'cuda', 'mps'). Auto-detects if not provided.
        """
        self.logger = logging.getLogger(__name__)
        self.device = self._get_device(device)
        self.model_path = model_path or self.MODEL_NAME
        self._pipeline: Optional[Pipeline] = None
    
    def _get_device(self, device: Optional[str]) -> str:
        """Determine the best available device."""
        if device:
            return device
        
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    @property
    def pipeline(self) -> Pipeline:
        """Lazy load the NER pipeline."""
        if self._pipeline is None:
            self._load_model()
        return self._pipeline
    
    def _load_model(self):
        """Load the NER model and create pipeline."""
        try:
            self.logger.info(f"Loading NER model from {self.model_path}")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                model_max_length=512
            )
            model = AutoModelForTokenClassification.from_pretrained(self.model_path)
            
            # Create pipeline
            self._pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                device=0 if self.device == "cuda" else -1,
                aggregation_strategy="simple"
            )
            
            self.logger.info(f"NER model loaded successfully on {self.device}")
            
        except Exception as e:
            self.logger.error(f"Failed to load NER model: {e}")
            raise RuntimeError(f"Failed to load NER model: {e}")
    
    def detect(self, text: str, confidence_threshold: float = 0.85) -> List[Tuple[str, str, int, int, float]]:
        """
        Detect PII entities in text using NER.
        
        Args:
            text: Input text to analyze
            confidence_threshold: Minimum confidence score for detection
            
        Returns:
            List of tuples (entity_type, matched_text, start_pos, end_pos, confidence_score)
        """
        if not text:
            return []
        
        detections = []
        
        try:
            # Run NER pipeline
            entities = self.pipeline(text)
            
            # Process entities
            for entity in entities:
                # Check if entity type is in our list of PII entities
                entity_type = entity.get("entity_group", "").upper()
                if not any(ent in entity_type for ent in self.DETECTED_ENTITIES):
                    continue
                
                # Check confidence threshold
                score = entity.get("score", 0.0)
                if score < confidence_threshold:
                    continue
                
                # Normalize entity type
                normalized_type = self._normalize_entity_type(entity_type)
                
                detections.append((
                    normalized_type,
                    entity["word"].strip(),
                    entity["start"],
                    entity["end"],
                    score
                ))
            
        except Exception as e:
            self.logger.error(f"Error during NER detection: {e}")
            # Return empty list on error to maintain privacy-first principle
            return []
        
        return self._merge_adjacent_entities(detections)
    
    def _normalize_entity_type(self, entity_type: str) -> str:
        """Normalize entity types to standard names."""
        entity_type = entity_type.upper()
        
        if "PER" in entity_type:
            return "PERSON"
        elif "LOC" in entity_type:
            return "LOCATION"
        elif "ORG" in entity_type:
            return "ORGANIZATION"
        else:
            return entity_type
    
    def _merge_adjacent_entities(self, detections: List[Tuple[str, str, int, int, float]]) -> List[Tuple[str, str, int, int, float]]:
        """Merge adjacent entities of the same type."""
        if not detections:
            return []
        
        # Sort by start position
        sorted_detections = sorted(detections, key=lambda x: x[2])
        
        merged = []
        current = list(sorted_detections[0])
        
        for detection in sorted_detections[1:]:
            # Check if adjacent and same type
            if (detection[2] - current[3] <= 1 and 
                detection[0] == current[0]):
                # Merge: extend the text and end position, keep higher confidence
                current[1] = current[1] + " " + detection[1]
                current[3] = detection[3]
                current[4] = max(current[4], detection[4])
            else:
                merged.append(tuple(current))
                current = list(detection)
        
        merged.append(tuple(current))
        
        return merged
    
    def download_model(self, target_dir: str):
        """
        Download model for offline use.
        
        Args:
            target_dir: Directory to save the model
        """
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Downloading NER model to {target_path}")
        
        # Download tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        model = AutoModelForTokenClassification.from_pretrained(self.MODEL_NAME)
        
        # Save to target directory
        tokenizer.save_pretrained(target_path)
        model.save_pretrained(target_path)
        
        self.logger.info("Model downloaded successfully")