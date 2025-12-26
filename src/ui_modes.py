"""
Three operating modes for optimal resource management.
"""

import logging
import gc
from pathlib import Path
from typing import Dict, Any, Optional

from transcription import VoskTranscriber
from correction import CorrectionManager
from file_manager import FileManager
from utils import get_timestamp, validate_filename, format_file_size
from shortcuts import ShortcutHandler, show_quick_actions_bar
from export_formats import ExportManager
from performance import optimize_memory, ProgressBar

logger = logging.getLogger("vosk_stt.modes")

def show_mode_selection() -> str:
    """
    Show mode selection menu with shortcuts.
    
    Returns:
        User's choice
    """
    show_quick_actions_bar()
    print("\n" + "="*60)
    print("SELECT OPERATING MODE")
    print("="*60)
    print("[T] 1. Transcribe Only (Vosk: ON, Ollama: OFF)")
    print("       → Record audio to text, save file")
    print("       → Memory: ~6-8GB")
    print()
    print("[C] 2. Correct Only (Vosk: OFF, Ollama: ON)")
    print("       → Fix existing transcription files with AI")
    print("       → Memory: ~4-5GB")
    print()
    print("[F] 3. Full Workflow (Sequential loading)")
    print("       → Record → Save → Unload Vosk → Load Ollama → Correct")
    print("       → Memory: ~6-8GB max (never both loaded)")
    print()
    print("[O] 4. File Operations (No models needed)")
    print("       → View, search, delete, merge files")
    print("       → Memory: ~100-200MB")
    print()
    print("[S] 5. Settings & Tools")
    print("[V] 6. View Options Tree")
    print("[M] 7. Check Memory Status")
    print("[Q] 0. Exit")
    print("="*60)
    print("Tip: Type letter shortcuts (T/C/F/O/S) or numbers (1-7)")
    
    return ShortcutHandler.get_input_with_shortcuts("\nChoice: ")


class BaseMode:
    """Base class for operating modes."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.file_manager = FileManager(config['output']['folder'])
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def cleanup(self):
        """Clean up resources."""
        gc.collect()
        logger.info(f"Cleaned up {self.__class__.__name__}")


class TranscribeOnlyMode(BaseMode):
    """Mode 1: Transcription only, no AI correction."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.transcriber = None
        self.export_manager = ExportManager(config['output']['folder'])
    
    def run(self):
        """Run transcription-only workflow."""
        # Initialize transcriber
        self.transcriber = VoskTranscriber(
            model_path=self.config['vosk']['model_path'],
            sample_rate=self.config['vosk']['sample_rate'],
            buffer_size=self.config['vosk']['buffer_size']
        )
        
        # Load model
        if not self.transcriber.load_model():
            print("\n✗ Failed to load Vosk model")
            return
        
        # Show menu
        while True:
            print("\n" + "="*60)
            print("TRANSCRIPTION MENU")
            print("="*60)
            print("1. Quick transcription (default settings)")
            print("2. Custom filename transcription")
            print("3. Append to existing file")
            print("0. Back to mode selection")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._quick_transcription()
            elif choice == '2':
                self._custom_transcription()
            elif choice == '3':
                self._append_transcription()
            else:
                print("Invalid choice")
    
    def _quick_transcription(self):
        """Quick transcription with defaults."""
        filename = f"transcription_{get_timestamp()}.txt"
        self._record_and_save(filename, 'w', 'txt')
    
    def _custom_transcription(self):
        """Transcription with custom filename."""
        filename = input("\nEnter filename (without extension): ").strip()
        if not filename:
            filename = f"transcription_{get_timestamp()}"
        filename = validate_filename(filename)
        
        print("\nFormat:")
        print("1. Plain text (.txt)")
        print("2. Markdown (.md)")
        print("3. Timestamped (.txt)")
        format_choice = input("Choice (1-3): ").strip() or '1'
        
        format_type = {'1': 'txt', '2': 'md', '3': 'timestamped'}.get(format_choice, 'txt')
        self._record_and_save(f"{filename}.txt", 'w', format_type)
    
    def _append_transcription(self):
        """Append to existing file."""
        files = self.file_manager.list_files("*.txt")
        if not files:
            print("\nNo files to append to")
            return
        
        print("\nExisting files:")
        for i, f in enumerate(files, 1):
            print(f"{i}. {f.name}")
        
        try:
            choice = int(input(f"\nSelect (1-{len(files)}, 0=cancel): ").strip())
            if choice == 0:
                return
            if 1 <= choice <= len(files):
                self._record_and_save(files[choice-1].name, 'a', 'txt')
        except ValueError:
            print("Invalid input")
    
    def _record_and_save(self, filename: str, mode: str, format_type: str):
        """Record audio and save transcription with export options."""
        from performance import optimize_model_loading, cleanup_after_model
        
        auto_save_interval = self.config['output'].get('auto_save_interval')
        filepath = Path(self.config['output']['folder']) / filename
        
        def save_callback():
            content = self.transcriber.get_full_text()
            self.file_manager.write_file(content, filename, format_type, mode)
        
        # Optimize for model usage
        optimize_model_loading()
        
        # Record
        transcription = self.transcriber.transcribe(
            auto_save_interval=auto_save_interval,
            save_callback=save_callback
        )
        
        # Cleanup after transcription
        cleanup_after_model()
        
        if not transcription:
            print("\n⚠ No speech detected")
            return
        
        # Save final
        full_text = self.transcriber.get_full_text()
        saved_path = self.file_manager.write_file(full_text, filename, format_type, mode)
        
        if saved_path:
            action = "Appended to" if mode == 'a' else "Saved to"
            print(f"\n✓ {action}: {saved_path.name}")
            print(f"Words: {self.transcriber.get_word_count():,}")
            
            # Ask for additional export formats
            export_more = input("\nExport to additional formats? (yes/no): ").strip().lower()
            if export_more in ['yes', 'y']:
                self._export_to_formats(full_text, saved_path.stem)
    
    def _export_to_formats(self, content: str, base_filename: str):
        """Export to multiple formats."""
        while True:
            format_choice = self.export_manager.show_export_menu()
            
            if format_choice:
                exported = self.export_manager.export(content, base_filename, format_choice)
                if exported:
                    print(f"\n✓ Exported to: {exported.name}")
            
            another = input("\nExport to another format? (yes/no): ").strip().lower()
            if another not in ['yes', 'y']:
                break
    
    def cleanup(self):
        """Clean up transcriber with memory optimization."""
        if self.transcriber:
            del self.transcriber
        optimize_memory()
        super().cleanup()


class CorrectOnlyMode(BaseMode):
    """Mode 2: AI correction only, no transcription."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.correction_manager = CorrectionManager(config, self.file_manager)
    
    def run(self):
        """Run correction-only workflow."""
        while True:
            print("\n" + "="*60)
            print("CORRECTION MENU")
            print("="*60)
            print("1. Correct single file (interactive)")
            print("2. Correct single file (quick)")
            print("3. Batch correct multiple files")
            print("4. View files")
            print("0. Back to mode selection")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._interactive_correction()
            elif choice == '2':
                self._quick_correction()
            elif choice == '3':
                self._batch_correction()
            elif choice == '4':
                self._view_files()
            else:
                print("Invalid choice")
    
    def _interactive_correction(self):
        """Interactive correction with options."""
        files = self._get_correctable_files()
        if not files:
            return
        
        filepath = self._select_file(files)
        if filepath:
            self.correction_manager.interactive_correct(filepath)
    
    def _quick_correction(self):
        """Quick correction with defaults."""
        files = self._get_correctable_files()
        if not files:
            return
        
        filepath = self._select_file(files)
        if filepath:
            self.correction_manager.correct_file(filepath, show_live=True)
    
    def _batch_correction(self):
        """Batch correct multiple files."""
        files = self._get_correctable_files()
        if not files:
            return
        
        print("\nEnter file numbers (e.g., 1 3 5) or 'all': ")
        selection = input("> ").strip()
        
        if selection.lower() == 'all':
            files_to_correct = files
        else:
            try:
                indices = [int(x) - 1 for x in selection.split()]
                files_to_correct = [files[i] for i in indices if 0 <= i < len(files)]
            except ValueError:
                print("Invalid input")
                return
        
        if files_to_correct:
            self.correction_manager.batch_correct(files_to_correct, show_live=False)
    
    def _view_files(self):
        """View all transcription files."""
        files = self.file_manager.list_files()
        if not files:
            print("\nNo files found")
            return
        
        print("\n" + "="*60)
        print(f"TRANSCRIPTION FILES ({len(files)})")
        print("="*60)
        
        for i, filepath in enumerate(files, 1):
            info = self.file_manager.get_file_info(filepath)
            print(f"\n{i}. {info['name']}")
            print(f"   Size: {format_file_size(info['size'])} | Words: {info['word_count']:,}")
    
    def _get_correctable_files(self):
        """Get list of files that can be corrected."""
        files = self.file_manager.list_files("*.txt") + self.file_manager.list_files("*.md")
        if not files:
            print("\nNo files available for correction")
        return files
    
    def _select_file(self, files):
        """Select a file from list."""
        print("\nFiles:")
        for i, f in enumerate(files, 1):
            info = self.file_manager.get_file_info(f)
            print(f"{i}. {f.name} ({format_file_size(info['size'])})")
        
        try:
            choice = int(input(f"\nSelect (1-{len(files)}, 0=cancel): ").strip())
            if choice == 0:
                return None
            if 1 <= choice <= len(files):
                return files[choice - 1]
        except ValueError:
            print("Invalid input")
        return None
    
    def cleanup(self):
        """Clean up correction manager."""
        # Stop Ollama if configured
        if self.config.get('ai', {}).get('auto_stop_ollama', False):
            self.correction_manager.ollama.stop()
        super().cleanup()


class FullWorkflowMode(BaseMode):
    """Mode 3: Full workflow with optimized memory usage."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.transcriber = None
        self.correction_manager = None
    
    def run(self):
        """Run full workflow with sequential loading."""
        print("\n" + "="*60)
        print("FULL WORKFLOW - MEMORY OPTIMIZED")
        print("="*60)
        print("Step 1: Load Vosk and transcribe")
        print("Step 2: Unload Vosk, free memory")
        print("Step 3: Load Ollama and correct")
        print("="*60)
        
        proceed = input("\nProceed? (yes/no): ").strip().lower()
        if proceed not in ['yes', 'y']:
            return
        
        # STEP 1: Transcribe
        print("\n" + "="*60)
        print("STEP 1: TRANSCRIPTION")
        print("="*60)
        
        self.transcriber = VoskTranscriber(
            model_path=self.config['vosk']['model_path'],
            sample_rate=self.config['vosk']['sample_rate'],
            buffer_size=self.config['vosk']['buffer_size']
        )
        
        if not self.transcriber.load_model():
            print("\n✗ Failed to load Vosk model")
            return
        
        # Get filename
        filename = input("\nEnter filename (or Enter for default): ").strip()
        if not filename:
            filename = f"transcription_{get_timestamp()}"
        filename = validate_filename(filename) + ".txt"
        
        # Record
        auto_save_interval = self.config['output'].get('auto_save_interval')
        filepath = Path(self.config['output']['folder']) / filename
        
        def save_callback():
            content = self.transcriber.get_full_text()
            self.file_manager.write_file(content, filename, 'txt', 'w')
        
        transcription = self.transcriber.transcribe(
            auto_save_interval=auto_save_interval,
            save_callback=save_callback
        )
        
        if not transcription:
            print("\n⚠ No speech detected")
            return
        
        # Save
        full_text = self.transcriber.get_full_text()
        saved_path = self.file_manager.write_file(full_text, filename, 'txt', 'w')
        
        if not saved_path:
            print("\n✗ Failed to save transcription")
            return
        
        print(f"\n✓ Transcription saved: {saved_path.name}")
        print(f"Words: {len(full_text.split()):,}")
        
        # STEP 2: Unload Vosk
        print("\n" + "="*60)
        print("STEP 2: FREEING MEMORY")
        print("="*60)
        print("Unloading Vosk model...")
        
        del self.transcriber
        self.transcriber = None
        gc.collect()
        
        print("✓ Memory freed")
        
        import time
        time.sleep(2)  # Give system time to release memory
        
        # STEP 3: Correct
        print("\n" + "="*60)
        print("STEP 3: AI CORRECTION")
        print("="*60)
        
        self.correction_manager = CorrectionManager(self.config, self.file_manager)
        
        print("\nStarting AI correction...")
        self.correction_manager.correct_file(saved_path, show_live=True)
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
    
    def cleanup(self):
        """Clean up both components."""
        if self.transcriber:
            del self.transcriber
        if self.correction_manager:
            if self.config.get('ai', {}).get('auto_stop_ollama', False):
                self.correction_manager.ollama.stop()
        super().cleanup()
