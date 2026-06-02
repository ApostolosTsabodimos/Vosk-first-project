"""
AI-powered transcription correction workflows.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from ollama_manager import OllamaManager
from file_manager import FileManager
from utils import show_diff, format_file_size
from cache_manager import get_cache

logger = logging.getLogger("vosk_stt.correction")

class CorrectionManager:
    """Manages AI correction workflows."""
    
    def __init__(self, config: Dict[str, Any], file_manager: FileManager):
        """
        Initialize correction manager.
        
        Args:
            config: Application configuration
            file_manager: FileManager instance
        """
        self.config = config
        self.file_manager = file_manager
        self.cache = get_cache()
        
        # Initialize Ollama manager
        ai_config = config.get('ai', {})
        self.ollama = OllamaManager(
            model=ai_config.get('model', 'mistral'),
            auto_start=ai_config.get('auto_start_ollama', True)
        )
        
        self.temperature = ai_config.get('temperature', 0.3)
        self.show_live = ai_config.get('show_live', True)
        self.prompt_template = config.get('correction_prompt', None)
        
        logger.info("CorrectionManager initialized")
    
    def correct_text(
        self,
        text: str,
        show_live: Optional[bool] = None,
        temperature: Optional[float] = None,
        custom_prompt: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Correct text using AI with caching.
        
        Args:
            text: Text to correct
            show_live: Show live processing (uses config default if None)
            temperature: AI temperature (uses config default if None)
            custom_prompt: Custom prompt template
            use_cache: Whether to use cached results
            
        Returns:
            Corrected text, or None if failed
        """
        if show_live is None:
            show_live = self.show_live
        
        if temperature is None:
            temperature = self.temperature
        
        # Check cache first
        if use_cache:
            model = self.ollama.model
            cached = self.cache.correction_cache.get(text, temperature, model)
            if cached:
                self.cache.record_hit()
                print("\n✓ Using cached correction")
                logger.info(f"Cache hit for correction ({len(text)} chars)")
                return cached
            self.cache.record_miss()
        
        prompt_template = custom_prompt or self.prompt_template
        
        logger.info(f"Correcting {len(text)} chars with temp={temperature}, live={show_live}")
        
        corrected = self.ollama.correct_text(
            text=text,
            temperature=temperature,
            prompt_template=prompt_template,
            stream=show_live
        )
        
        # Cache the result
        if corrected and use_cache:
            self.cache.correction_cache.put(text, temperature, self.ollama.model, corrected)
        
        return corrected
    
    def correct_file(
        self,
        filepath: Path,
        show_live: bool = True,
        save: bool = True,
        show_preview: bool = True
    ) -> Optional[Path]:
        """
        Correct an existing file.
        
        Args:
            filepath: Path to file to correct
            show_live: Show live AI processing
            save: Save corrected version
            show_preview: Show preview before saving
            
        Returns:
            Path to corrected file if saved, None otherwise
        """
        logger.info(f"Correcting file: {filepath.name}")
        
        # Read original
        original_text = self.file_manager.read_file(filepath)
        if not original_text:
            print(f"✗ Failed to read {filepath.name}")
            return None
        
        file_info = self.file_manager.get_file_info(filepath)
        print(f"\nFile: {filepath.name}")
        print(f"Size: {format_file_size(file_info['size'])}")
        print(f"Words: {file_info['word_count']:,}")
        
        # Correct
        corrected_text = self.correct_text(original_text, show_live=show_live)
        
        if not corrected_text:
            print("✗ Correction failed")
            return None
        
        # Show differences
        show_diff(original_text, corrected_text)
        
        # Preview
        if show_preview:
            preview_len = self.config.get('ui', {}).get('preview_length', 500)
            print("\n" + "="*60)
            print(f"PREVIEW (first {preview_len} chars)")
            print("="*60)
            print(corrected_text[:preview_len])
            if len(corrected_text) > preview_len:
                print("...")
            print("="*60)
        
        # Save
        if save:
            if self.config.get('ui', {}).get('confirm_before_save', True):
                confirm = input("\nSave corrected version? (yes/no): ").strip().lower()
                if confirm not in ['yes', 'y']:
                    print("✗ Not saved")
                    return None
            
            corrected_path = self.file_manager.get_corrected_filename(filepath)
            
            with open(corrected_path, 'w', encoding='utf-8') as f:
                f.write(corrected_text)
            
            print(f"\n✓ Saved: {corrected_path.name}")
            logger.info(f"Saved corrected file: {corrected_path.name}")
            return corrected_path
        
        return None
    
    def batch_correct(
        self,
        filepaths: list[Path],
        show_live: bool = False
    ) -> Dict[Path, Optional[Path]]:
        """
        Correct multiple files in batch.
        
        Args:
            filepaths: List of files to correct
            show_live: Show live processing (not recommended for batch)
            
        Returns:
            Dictionary mapping original paths to corrected paths
        """
        results = {}
        total = len(filepaths)
        
        print(f"\n{'='*60}")
        print(f"BATCH CORRECTION: {total} files")
        print(f"{'='*60}\n")
        
        for i, filepath in enumerate(filepaths, 1):
            print(f"\n[{i}/{total}] Processing: {filepath.name}")
            
            try:
                corrected_path = self.correct_file(
                    filepath,
                    show_live=show_live,
                    save=True,
                    show_preview=False
                )
                results[filepath] = corrected_path
                
                if corrected_path:
                    print(f"✓ Completed: {filepath.name}")
                else:
                    print(f"✗ Failed: {filepath.name}")
                    
            except Exception as e:
                logger.error(f"Error correcting {filepath.name}: {e}", exc_info=True)
                print(f"✗ Error: {e}")
                results[filepath] = None
        
        # Summary
        successful = sum(1 for v in results.values() if v is not None)
        print(f"\n{'='*60}")
        print(f"BATCH COMPLETE: {successful}/{total} successful")
        print(f"{'='*60}")
        
        logger.info(f"Batch correction complete: {successful}/{total} successful")
        return results
    
    def interactive_correct(self, filepath: Path) -> Optional[Path]:
        """
        Interactive correction with options.
        
        Args:
            filepath: File to correct
            
        Returns:
            Path to corrected file if saved
        """
        print("\n" + "="*60)
        print("CORRECTION OPTIONS")
        print("="*60)
        print("1. Live processing (see AI thinking)")
        print("2. Silent processing (faster)")
        print("3. Custom prompt")
        print("4. Adjust temperature")
        print("0. Cancel")
        
        choice = input("\nChoice (0-4): ").strip()
        
        if choice == '0':
            return None
        
        show_live = True
        temperature = self.temperature
        custom_prompt = None
        
        if choice == '2':
            show_live = False
        
        elif choice == '3':
            print("\nEnter custom instructions:")
            print("(The text will be automatically included)")
            custom_instructions = input("> ").strip()
            
            if custom_instructions:
                custom_prompt = f"""{custom_instructions}

Text to correct:
{{text}}

Corrected text:"""
        
        elif choice == '4':
            print("\nTemperature controls correction style:")
            print("  0.0-0.3: Very conservative, minimal changes")
            print("  0.3-0.7: Balanced (recommended)")
            print("  0.7-1.0: More creative corrections")
            print(f"\nCurrent: {temperature}")
            
            try:
                temp_input = input("New temperature (0.0-2.0): ").strip()
                temperature = float(temp_input)
                temperature = max(0.0, min(2.0, temperature))
            except ValueError:
                print("Invalid input, using default")
        
        # Perform correction
        return self.correct_file(
            filepath,
            show_live=show_live,
            save=True,
            show_preview=True
        )
