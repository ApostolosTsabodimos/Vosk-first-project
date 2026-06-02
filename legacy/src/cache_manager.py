"""
Intelligent caching system for file operations and AI results.
"""

import logging
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict

logger = logging.getLogger("vosk_stt.cache")

class LRUCache:
    """Least Recently Used cache with size limit."""
    
    def __init__(self, max_size: int = 50, max_memory_mb: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items
            max_memory_mb: Maximum memory usage in MB
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory = 0
        logger.info(f"LRU Cache initialized: {max_size} items, {max_memory_mb}MB")
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            value, timestamp, size = self.cache[key]
            logger.debug(f"Cache HIT: {key}")
            return value
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def put(self, key: str, value: Any) -> None:
        """Put item in cache."""
        # Estimate size
        size = len(str(value).encode('utf-8'))
        
        # Remove old key if exists
        if key in self.cache:
            _, _, old_size = self.cache[key]
            self.current_memory -= old_size
            del self.cache[key]
        
        # Evict if necessary
        while (len(self.cache) >= self.max_size or 
               self.current_memory + size > self.max_memory_bytes):
            if not self.cache:
                break
            evicted_key, (_, _, evicted_size) = self.cache.popitem(last=False)
            self.current_memory -= evicted_size
            logger.debug(f"Cache EVICT: {evicted_key}")
        
        # Add new item
        self.cache[key] = (value, time.time(), size)
        self.current_memory += size
        logger.debug(f"Cache PUT: {key} ({size} bytes)")
    
    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
        self.current_memory = 0
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'items': len(self.cache),
            'memory_mb': self.current_memory / 1024 / 1024,
            'max_items': self.max_size,
            'max_memory_mb': self.max_memory_bytes / 1024 / 1024
        }


class FileCache:
    """Cache for file contents and metadata."""
    
    def __init__(self):
        self.content_cache = LRUCache(max_size=30, max_memory_mb=50)
        self.metadata_cache = LRUCache(max_size=100, max_memory_mb=10)
        logger.info("FileCache initialized")
    
    def get_content(self, filepath: Path) -> Optional[str]:
        """
        Get file content from cache.
        
        Args:
            filepath: Path to file
            
        Returns:
            File content or None if not cached/invalid
        """
        key = str(filepath)
        cached = self.content_cache.get(key)
        
        if cached:
            content, mtime = cached
            # Validate cache (check if file modified)
            if filepath.exists() and filepath.stat().st_mtime == mtime:
                return content
            else:
                # Invalid cache, remove
                logger.debug(f"Cache invalidated: {filepath.name}")
        
        return None
    
    def put_content(self, filepath: Path, content: str) -> None:
        """
        Cache file content.
        
        Args:
            filepath: Path to file
            content: File content
        """
        if filepath.exists():
            key = str(filepath)
            mtime = filepath.stat().st_mtime
            self.content_cache.put(key, (content, mtime))
    
    def get_metadata(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Get file metadata from cache."""
        key = str(filepath)
        cached = self.metadata_cache.get(key)
        
        if cached:
            metadata, mtime = cached
            if filepath.exists() and filepath.stat().st_mtime == mtime:
                return metadata
        
        return None
    
    def put_metadata(self, filepath: Path, metadata: Dict[str, Any]) -> None:
        """Cache file metadata."""
        if filepath.exists():
            key = str(filepath)
            mtime = filepath.stat().st_mtime
            self.metadata_cache.put(key, (metadata, mtime))
    
    def invalidate(self, filepath: Path) -> None:
        """Invalidate cache for a file."""
        key = str(filepath)
        if key in self.content_cache.cache:
            del self.content_cache.cache[key]
        if key in self.metadata_cache.cache:
            del self.metadata_cache.cache[key]
        logger.debug(f"Cache invalidated for: {filepath.name}")
    
    def clear(self) -> None:
        """Clear all caches."""
        self.content_cache.clear()
        self.metadata_cache.clear()
        logger.info("FileCache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'content': self.content_cache.stats(),
            'metadata': self.metadata_cache.stats()
        }


class CorrectionCache:
    """Cache for AI correction results."""
    
    def __init__(self):
        self.cache = LRUCache(max_size=20, max_memory_mb=100)
        logger.info("CorrectionCache initialized")
    
    def _get_hash(self, text: str, temperature: float, model: str) -> str:
        """Generate cache key from text and parameters."""
        key_str = f"{text}|{temperature}|{model}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, text: str, temperature: float, model: str) -> Optional[str]:
        """
        Get cached correction.
        
        Args:
            text: Original text
            temperature: AI temperature
            model: Model name
            
        Returns:
            Corrected text or None
        """
        key = self._get_hash(text, temperature, model)
        return self.cache.get(key)
    
    def put(self, text: str, temperature: float, model: str, corrected: str) -> None:
        """
        Cache correction result.
        
        Args:
            text: Original text
            temperature: AI temperature
            model: Model name
            corrected: Corrected text
        """
        key = self._get_hash(text, temperature, model)
        self.cache.put(key, corrected)
        logger.info(f"Cached correction (hash: {key[:8]}...)")
    
    def clear(self) -> None:
        """Clear correction cache."""
        self.cache.clear()
        logger.info("CorrectionCache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.stats()


class CacheManager:
    """
    Central cache management.
    Coordinates all caching systems.
    """
    
    def __init__(self):
        self.file_cache = FileCache()
        self.correction_cache = CorrectionCache()
        self._hits = 0
        self._misses = 0
        logger.info("CacheManager initialized")
    
    def record_hit(self):
        """Record cache hit."""
        self._hits += 1
    
    def record_miss(self):
        """Record cache miss."""
        self._misses += 1
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._hits + self._misses
        return (self._hits / total * 100) if total > 0 else 0.0
    
    def clear_all(self) -> None:
        """Clear all caches."""
        self.file_cache.clear()
        self.correction_cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("All caches cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            'file_cache': self.file_cache.stats(),
            'correction_cache': self.correction_cache.stats(),
            'hit_rate': f"{self.get_hit_rate():.1f}%",
            'total_hits': self._hits,
            'total_misses': self._misses
        }
    
    def print_stats(self) -> None:
        """Print cache statistics."""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("CACHE STATISTICS")
        print("="*60)
        print(f"Hit Rate: {stats['hit_rate']}")
        print(f"Total Hits: {stats['total_hits']}")
        print(f"Total Misses: {stats['total_misses']}")
        
        print("\nFile Cache:")
        fc = stats['file_cache']
        print(f"  Content: {fc['content']['items']} items, "
              f"{fc['content']['memory_mb']:.1f}MB")
        print(f"  Metadata: {fc['metadata']['items']} items, "
              f"{fc['metadata']['memory_mb']:.1f}MB")
        
        print("\nCorrection Cache:")
        cc = stats['correction_cache']
        print(f"  Items: {cc['items']}, "
              f"Memory: {cc['memory_mb']:.1f}MB")
        print("="*60)


# Global cache instance
_global_cache = None

def get_cache() -> CacheManager:
    """Get global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache
