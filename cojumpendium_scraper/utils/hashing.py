"""File hashing utilities for deduplication."""

import hashlib
from pathlib import Path


def hash_file(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate hash of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha256, etc.)
        
    Returns:
        Hex digest of file hash
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def hash_bytes(data: bytes, algorithm: str = 'sha256') -> str:
    """Calculate hash of bytes.
    
    Args:
        data: Bytes to hash
        algorithm: Hash algorithm
        
    Returns:
        Hex digest of hash
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data)
    return hash_obj.hexdigest()


def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Calculate hash of string.
    
    Args:
        text: String to hash
        algorithm: Hash algorithm
        
    Returns:
        Hex digest of hash
    """
    return hash_bytes(text.encode('utf-8'), algorithm)
