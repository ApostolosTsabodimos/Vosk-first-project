"""
File management operations for transcriptions with intelligent caching.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from cache_manager import get_cache

logger = logging.getLogger("vosk_stt.filemanager")

class FileManager:
    """Manages transcription file operations with caching."""
    
    def __init__(self, output_folder: str):
        """
        Initialize file manager.
        
        Args:
            output_folder: Path to transcription folder
        """
        self.output_folder = Path(output_folder).expanduser()
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.cache = get_cache()
        logger.info(f"FileManager initialized with folder: {self.output_folder}")
    
    def list_files(self, pattern: str = "*") -> List[Path]:
        """
        List files in output folder.
        
        Args:
            pattern: Glob pattern for filtering
            
        Returns:
            List of file paths
        """
        files = sorted(self.output_folder.glob(pattern))
        files = [f for f in files if f.is_file()]
        logger.debug(f"Found {len(files)} files matching '{pattern}'")
        return files
    
    def get_file_info(self, filepath: Path) -> dict:
        """
        Get detailed file information with caching.
        
        Args:
            filepath: Path to file
            
        Returns:
            Dictionary with file metadata
        """
        # Try cache first
        cached = self.cache.file_cache.get_metadata(filepath)
        if cached:
            self.cache.record_hit()
            logger.debug(f"Cache hit for metadata: {filepath.name}")
            return cached
        
        self.cache.record_miss()
        
        # Compute metadata
        stat = filepath.stat()
        
        # Get word count
        try:
            content = self.read_file(filepath)
            if content:
                word_count = len(content.split())
                char_count = len(content)
            else:
                word_count = 0
                char_count = 0
        except Exception as e:
            logger.warning(f"Error reading {filepath}: {e}")
            word_count = 0
            char_count = 0
        
        metadata = {
            'name': filepath.name,
            'path': filepath,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'word_count': word_count,
            'char_count': char_count
        }
        
        # Cache it
        self.cache.file_cache.put_metadata(filepath, metadata)
        
        return metadata
    
    def delete_file(self, filepath: Path) -> bool:
        """
        Delete a file and invalidate cache.
        
        Args:
            filepath: Path to file to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            filepath.unlink()
            self.cache.file_cache.invalidate(filepath)
            logger.info(f"Deleted file: {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {filepath}: {e}")
            return False
    
    def search_files(self, search_term: str, case_sensitive: bool = False) -> List[Tuple[Path, str]]:
        """
        Search for text across all files.
        
        Args:
            search_term: Text to search for
            case_sensitive: Whether to match case
            
        Returns:
            List of (filepath, context) tuples
        """
        results = []
        files = self.list_files("*.txt") + self.list_files("*.md")
        
        logger.info(f"Searching {len(files)} files for '{search_term}'")
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                search_content = content if case_sensitive else content.lower()
                search_term_normalized = search_term if case_sensitive else search_term.lower()
                
                if search_term_normalized in search_content:
                    # Extract context
                    words = content.split()
                    for i, word in enumerate(words):
                        word_normalized = word if case_sensitive else word.lower()
                        if search_term_normalized in word_normalized:
                            start = max(0, i - 5)
                            end = min(len(words), i + 6)
                            context = ' '.join(words[start:end])
                            results.append((filepath, context))
                            break
                            
            except Exception as e:
                logger.warning(f"Error searching {filepath}: {e}")
        
        logger.info(f"Found {len(results)} matches")
        return results
    
    def merge_files(self, filepaths: List[Path], output_name: Optional[str] = None) -> Optional[Path]:
        """
        Merge multiple files into one.
        
        Args:
            filepaths: List of files to merge
            output_name: Name for merged file (auto-generated if None)
            
        Returns:
            Path to merged file, or None if failed
        """
        if not filepaths:
            logger.warning("No files to merge")
            return None
        
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"merged_{timestamp}.txt"
        
        output_path = self.output_folder / output_name
        
        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for i, filepath in enumerate(filepaths, 1):
                    outfile.write(f"\n\n{'='*60}\n")
                    outfile.write(f"Source {i}: {filepath.name}\n")
                    outfile.write(f"{'='*60}\n\n")
                    
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
            
            logger.info(f"Merged {len(filepaths)} files into {output_name}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to merge files: {e}")
            return None
    
    def read_file(self, filepath: Path) -> Optional[str]:
        """
        Read file content with caching.
        
        Args:
            filepath: Path to file
            
        Returns:
            File content, or None if failed
        """
        # Try cache first
        cached = self.cache.file_cache.get_content(filepath)
        if cached:
            self.cache.record_hit()
            logger.debug(f"Cache hit for content: {filepath.name}")
            return cached
        
        self.cache.record_miss()
        
        # Read from disk
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cache it
            self.cache.file_cache.put_content(filepath, content)
            logger.debug(f"Read and cached: {filepath.name} ({len(content)} chars)")
            
            return content
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return None
    
    def write_file(
        self,
        content: str,
        filename: str,
        format_type: str = 'txt',
        mode: str = 'w'
    ) -> Optional[Path]:
        """
        Write content to file.
        
        Args:
            content: Content to write
            filename: Output filename (without extension)
            format_type: File format (txt, md, timestamped)
            mode: Write mode ('w' for write, 'a' for append)
            
        Returns:
            Path to written file, or None if failed
        """
        # Add extension if not present
        if not filename.endswith(('.txt', '.md')):
            ext = '.md' if format_type == 'md' else '.txt'
            filename = f"{filename}{ext}"
        
        filepath = self.output_folder / filename
        
        try:
            with open(filepath, mode, encoding='utf-8') as f:
                if mode == 'a' and filepath.exists():
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f'\n\n--- Session: {timestamp} ---\n')
                
                # Format content based on type
                if format_type == 'md':
                    if mode == 'w':
                        f.write('# Transcription\n\n')
                    f.write(content)
                elif format_type == 'timestamped':
                    self._write_timestamped(f, content)
                else:
                    f.write(content)
            
            logger.info(f"Wrote {len(content)} chars to {filepath.name}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")
            return None
    
    def _write_timestamped(self, file_handle, content: str) -> None:
        """Write content with timestamps."""
        sentences = content.split('. ')
        for i, sentence in enumerate(sentences):
            if i % 5 == 0:  # Timestamp every 5 sentences
                timestamp = datetime.now().strftime('%H:%M:%S')
                file_handle.write(f"\n[{timestamp}] ")
            file_handle.write(sentence)
            if sentence and not sentence.endswith('.'):
                file_handle.write('. ')
    
    def get_corrected_filename(self, original_path: Path) -> Path:
        """
        Generate filename for corrected version.
        
        Args:
            original_path: Path to original file
            
        Returns:
            Path for corrected file
        """
        stem = original_path.stem
        suffix = original_path.suffix
        corrected_name = f"{stem}_corrected{suffix}"
        return self.output_folder / corrected_name
