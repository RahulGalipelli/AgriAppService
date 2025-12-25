"""
Image Hashing Service for Consistent Plant Disease Detection
Uses perceptual hashing to identify duplicate/similar images
"""
import hashlib
from typing import Optional, Tuple
from PIL import Image
import io
import imagehash


class ImageHashService:
    """Service for generating and comparing image hashes"""
    
    @staticmethod
    def generate_hash(image_bytes: bytes) -> Tuple[str, str]:
        """
        Generate multiple hash types for better matching
        
        Returns:
            Tuple of (perceptual_hash, average_hash)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Perceptual hash (pHash) - good for similar images
            phash = str(imagehash.phash(image))
            
            # Average hash - good for general similarity
            avg_hash = str(imagehash.average_hash(image))
            
            return phash, avg_hash
        except Exception as e:
            raise ValueError(f"Failed to generate image hash: {str(e)}")
    
    @staticmethod
    def calculate_similarity(hash1: str, hash2: str) -> float:
        """
        Calculate similarity between two hashes (0-1, where 1 is identical)
        """
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            # Hamming distance (lower = more similar)
            distance = h1 - h2
            # Convert to similarity score (0-1)
            # Max distance for 64-bit hash is 64
            similarity = 1 - (distance / 64.0)
            return max(0.0, similarity)
        except Exception:
            return 0.0
    
    @staticmethod
    def generate_md5(image_bytes: bytes) -> str:
        """Generate MD5 hash for exact duplicate detection"""
        return hashlib.md5(image_bytes).hexdigest()

