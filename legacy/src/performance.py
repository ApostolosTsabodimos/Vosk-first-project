"""
Performance optimization utilities.
"""

import gc
import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger("vosk_stt.performance")

def optimize_memory():
    """
    Force aggressive garbage collection and memory optimization.
    """
    logger.debug("Running memory optimization...")
    
    # Force collection of all generations
    collected = gc.collect()
    
    # Disable automatic GC temporarily for performance
    # (will be re-enabled when needed)
    gc.disable()
    
    logger.debug(f"Collected {collected} objects")
    
    # Re-enable after a moment
    import threading
    def re_enable():
        time.sleep(0.1)
        gc.enable()
    threading.Thread(target=re_enable, daemon=True).start()

def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

def lazy_import(module_name: str) -> Any:
    """
    Lazy import module only when needed.
    
    Args:
        module_name: Name of module to import
        
    Returns:
        Imported module
    """
    import importlib
    logger.debug(f"Lazy importing: {module_name}")
    return importlib.import_module(module_name)

class ProgressBar:
    """Simple progress bar for long operations."""
    
    def __init__(self, total: int, prefix: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.prefix = prefix
        self.width = width
        self.start_time = time.time()
    
    def update(self, amount: int = 1):
        """Update progress bar."""
        self.current += amount
        self._display()
    
    def _display(self):
        """Display current progress."""
        if self.total == 0:
            return
        
        percent = min(100, (self.current / self.total) * 100)
        filled = int(self.width * self.current / self.total)
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Calculate ETA
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f" ETA: {int(eta)}s"
        else:
            eta_str = ""
        
        print(f'\r{self.prefix} |{bar}| {percent:.1f}%{eta_str}', end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete
    
    def finish(self):
        """Mark as complete."""
        self.current = self.total
        self._display()

def batch_process(items: list, processor: Callable, batch_size: int = 10, 
                  show_progress: bool = True) -> list:
    """
    Process items in batches for better performance.
    
    Args:
        items: List of items to process
        processor: Function to process each item
        batch_size: Size of each batch
        show_progress: Show progress bar
        
    Returns:
        List of results
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    progress = ProgressBar(len(items), "Processing") if show_progress else None
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        
        for item in batch:
            try:
                result = processor(item)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                results.append(None)
            
            if progress:
                progress.update()
        
        # Light GC between batches
        if i % (batch_size * 3) == 0:
            gc.collect(generation=0)  # Only young objects
    
    if progress:
        progress.finish()
    
    return results

class MemoryMonitor:
    """Monitor memory usage during operations."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_usage = 0
    
    def __enter__(self):
        """Start monitoring."""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        self.start_usage = process.memory_info().rss / 1024 / 1024  # MB
        logger.debug(f"{self.name}: Starting memory: {self.start_usage:.1f} MB")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring and report."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            end_usage = process.memory_info().rss / 1024 / 1024  # MB
            delta = end_usage - self.start_usage
            
            logger.info(f"{self.name}: Memory delta: {delta:+.1f} MB (now {end_usage:.1f} MB)")
            
            if delta > 100:  # More than 100MB increase
                logger.warning(f"{self.name}: High memory usage!")
        except ImportError:
            logger.debug("psutil not available for memory monitoring")

def compress_text(text: str) -> bytes:
    """
    Compress text for storage (optional optimization).
    
    Args:
        text: Text to compress
        
    Returns:
        Compressed bytes
    """
    import zlib
    return zlib.compress(text.encode('utf-8'), level=6)

def decompress_text(compressed: bytes) -> str:
    """
    Decompress text.
    
    Args:
        compressed: Compressed bytes
        
    Returns:
        Original text
    """
    import zlib
    return zlib.decompress(compressed).decode('utf-8')

def optimize_model_loading():
    """
    Optimize environment for model loading.
    """
    # Disable GC during model loading (faster)
    gc.disable()
    
    # Set environment variables for better performance
    import os
    os.environ['OMP_NUM_THREADS'] = '4'  # Optimize threading
    os.environ['MKL_NUM_THREADS'] = '4'
    
    logger.debug("Model loading optimization applied")

def cleanup_after_model():
    """
    Cleanup after model usage.
    """
    # Re-enable GC
    gc.enable()
    
    # Force full collection
    gc.collect()
    
    logger.debug("Post-model cleanup complete")
