"""
Command-line user interface for Vosk Speech-to-Text.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from transcription import VoskTranscriber
from correction import CorrectionManager
from file_manager import FileManager
from utils import get_timestamp, validate_filename, format_file_size

logger = logging.getLogger("vosk_stt.ui")

class VoskCLI:
    """Command-line interface for Vosk application."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CLI.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize components
        self.file_manager = FileManager(config['output']['folder'])
        self.correction_manager = CorrectionManager(config, self.file_manager)
        self.transcriber = VoskTranscriber(
            model_path=config['vosk']['model_path'],
            sample_rate=config['vosk']['sample_rate'],
            buffer_size=config['vosk']['buffer_size']
        )
        
        logger.info("VoskCLI initialized")
    
    def run(self) -> None:
        """Main application loop."""
        print("\n" + "="*60)
        print("VOSK SPEECH-TO-TEXT PROFESSIONAL")
        print("="*60)
        
        # Load Vosk model
        if not self.transcriber.load_model():
            print("\n✗ Failed to load Vosk model")
            return
        
        # Main menu loop
        while True:
            choice = self.show_main_menu()
            
            if choice == '0':
                self._handle_exit()
                break
            elif choice == '1':
                self._handle_new_transcription()
            elif choice == '2':
                self._show_file_operations_menu()
            elif choice == '3':
                self._show_correction_menu()
            else:
                print("Invalid choice")
    
    def show_main_menu(self) -> str:
        """
        Show main menu and get user choice.
        
        Returns:
            User's choice as string
        """
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("1. Record new transcription")
        print("2. File operations →")
        print("3. AI correction →")
        print("0. Exit")
        
        return input("\nChoice: ").strip()
    
    def _handle_new_transcription(self) -> None:
        """Handle new transcription workflow."""
        print("\n" + "="*60)
        print("NEW TRANSCRIPTION")
        print("="*60)
        print("1. Quick start (default settings)")
        print("2. Custom filename")
        print("3. Append to existing file")
        print("0. Back")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '0':
            return
        
        # Determine filename and mode
        filename = None
        mode = 'w'
        format_type = self.config['output']['default_format']
        
        if choice == '2':
            filename = self._get_custom_filename()
            format_type = self._get_format_choice()
        
        elif choice == '3':
            filename, mode = self._select_file_for_append()
            if filename is None:
                return
        
        # Generate filename if not set
        if filename is None:
            filename = f"transcription_{get_timestamp()}.txt"
        
        filepath = Path(self.config['output']['folder']) / filename
        
        # Start transcription
        self._record_transcription(filepath, mode, format_type)
    
    def _record_transcription(
        self,
        filepath: Path,
        mode: str,
        format_type: str
    ) -> None:
        """Record and save transcription."""
        auto_save_interval = self.config['output'].get('auto_save_interval')
        
        # Create save callback
        def save_callback():
            content = self.transcriber.get_full_text()
            self.file_manager.write_file(
                content=content,
                filename=filepath.name,
                format_type=format_type,
                mode=mode
            )
        
        # Transcribe
        transcription = self.transcriber.transcribe(
            auto_save_interval=auto_save_interval,
            save_callback=save_callback
        )
        
        if not transcription:
            print("\n⚠ No speech detected")
            return
        
        # Save final version
        full_text = self.transcriber.get_full_text()
        saved_path = self.file_manager.write_file(
            content=full_text,
            filename=filepath.name,
            format_type=format_type,
            mode=mode
        )
        
        if saved_path:
            action = "Appended to" if mode == 'a' else "Saved to"
            print(f"\n✓ {action}: {saved_path.name}")
            
            if self.config.get('ui', {}).get('show_word_count', True):
                print(f"Words: {self.transcriber.get_word_count():,}")
            
            # Offer correction
            self._offer_correction(saved_path, full_text)
    
    def _offer_correction(self, filepath: Path, text: str) -> None:
        """Offer AI correction after transcription."""
        print("\n" + "="*60)
        print("CORRECTION OPTIONS")
        print("="*60)
        print("1. Correct with AI (live)")
        print("2. Correct with AI (silent)")
        print("3. Skip")
        
        choice = input("\nChoice: ").strip()
        
        if choice in ['1', '2']:
            show_live = (choice == '1')
            corrected = self.correction_manager.correct_text(text, show_live=show_live)
            
            if corrected:
                from utils import show_diff
                show_diff(text, corrected)
                
                corrected_path = self.file_manager.get_corrected_filename(filepath)
                with open(corrected_path, 'w', encoding='utf-8') as f:
                    f.write(corrected)
                
                print(f"\n✓ Corrected version saved: {corrected_path.name}")
    
    def _get_custom_filename(self) -> str:
        """Get custom filename from user."""
        filename = input("\nEnter filename (without extension): ").strip()
        
        if not filename:
            filename = f"transcription_{get_timestamp()}"
        
        filename = validate_filename(filename)
        return filename
    
    def _get_format_choice(self) -> str:
        """Get output format choice."""
        print("\nSelect format:")
        print("1. Plain text (.txt)")
        print("2. Markdown (.md)")
        print("3. Timestamped (.txt)")
        
        choice = input("Format (1-3, default 1): ").strip() or '1'
        
        if choice == '2':
            return 'md'
        elif choice == '3':
            return 'timestamped'
        return 'txt'
    
    def _select_file_for_append(self) -> tuple[Optional[str], str]:
        """Select file to append to."""
        files = self.file_manager.list_files("*.txt") + self.file_manager.list_files("*.md")
        
        if not files:
            print("\nNo files available to append to")
            return None, 'w'
        
        print("\nExisting files:")
        for i, filepath in enumerate(files, 1):
            info = self.file_manager.get_file_info(filepath)
            print(f"{i}. {filepath.name} ({format_file_size(info['size'])})")
        
        try:
            choice = int(input(f"\nSelect file (1-{len(files)}, 0 to cancel): ").strip())
            if choice == 0:
                return None, 'w'
            if 1 <= choice <= len(files):
                return files[choice - 1].name, 'a'
        except ValueError:
            pass
        
        print("Invalid selection")
        return None, 'w'
    
    def _show_file_operations_menu(self) -> None:
        """Show file operations submenu."""
        while True:
            print("\n" + "="*60)
            print("FILE OPERATIONS")
            print("="*60)
            print("1. View all files")
            print("2. Search files")
            print("3. Delete file")
            print("4. Merge files")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._view_files()
            elif choice == '2':
                self._search_files()
            elif choice == '3':
                self._delete_file()
            elif choice == '4':
                self._merge_files()
            else:
                print("Invalid choice")
    
    def _view_files(self) -> None:
        """Display all files with details."""
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
            print(f"   Modified: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _search_files(self) -> None:
        """Search for text in files."""
        search_term = input("\nEnter search term: ").strip()
        
        if not search_term:
            return
        
        results = self.file_manager.search_files(search_term)
        
        if not results:
            print(f"\n'{search_term}' not found in any files")
            return
        
        print(f"\nFound '{search_term}' in {len(results)} file(s):")
        
        for filepath, context in results:
            print(f"\n• {filepath.name}")
            print(f"  ...{context}...")
    
    def _delete_file(self) -> None:
        """Delete a file."""
        files = self.file_manager.list_files()
        
        if not files:
            print("\nNo files to delete")
            return
        
        print("\nFiles:")
        for i, filepath in enumerate(files, 1):
            print(f"{i}. {filepath.name}")
        
        try:
            choice = int(input(f"\nSelect file (1-{len(files)}, 0 to cancel): ").strip())
            if choice == 0:
                return
            
            if 1 <= choice <= len(files):
                filepath = files[choice - 1]
                confirm = input(f"Delete '{filepath.name}'? (yes/no): ").strip().lower()
                
                if confirm in ['yes', 'y']:
                    if self.file_manager.delete_file(filepath):
                        print(f"✓ Deleted: {filepath.name}")
                    else:
                        print("✗ Failed to delete")
        except ValueError:
            print("Invalid input")
    
    def _merge_files(self) -> None:
        """Merge multiple files."""
        files = self.file_manager.list_files()
        
        if len(files) < 2:
            print("\nNeed at least 2 files to merge")
            return
        
        print("\nAvailable files:")
        for i, filepath in enumerate(files, 1):
            print(f"{i}. {filepath.name}")
        
        selection = input("\nEnter file numbers to merge (e.g., 1 3 5): ").strip()
        
        try:
            indices = [int(x) - 1 for x in selection.split()]
            files_to_merge = [files[i] for i in indices if 0 <= i < len(files)]
            
            if not files_to_merge:
                print("No valid files selected")
                return
            
            merged_path = self.file_manager.merge_files(files_to_merge)
            
            if merged_path:
                print(f"\n✓ Files merged into: {merged_path.name}")
            else:
                print("✗ Merge failed")
        except ValueError:
            print("Invalid input")
    
    def _show_correction_menu(self) -> None:
        """Show AI correction submenu."""
        while True:
            print("\n" + "="*60)
            print("AI CORRECTION")
            print("="*60)
            print("1. Correct existing file")
            print("2. Batch correct multiple files")
            print("3. Interactive correction")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._correct_single_file()
            elif choice == '2':
                self._batch_correct()
            elif choice == '3':
                self._interactive_correction()
            else:
                print("Invalid choice")
    
    def _correct_single_file(self) -> None:
        """Correct a single file."""
        files = self.file_manager.list_files("*.txt") + self.file_manager.list_files("*.md")
        
        if not files:
            print("\nNo files to correct")
            return
        
        print("\nFiles:")
        for i, filepath in enumerate(files, 1):
            info = self.file_manager.get_file_info(filepath)
            print(f"{i}. {filepath.name} ({format_file_size(info['size'])})")
        
        try:
            choice = int(input(f"\nSelect file (1-{len(files)}, 0 to cancel): ").strip())
            if choice == 0:
                return
            
            if 1 <= choice <= len(files):
                filepath = files[choice - 1]
                self.correction_manager.correct_file(filepath, show_live=True)
        except ValueError:
            print("Invalid input")
    
    def _batch_correct(self) -> None:
        """Batch correct multiple files."""
        files = self.file_manager.list_files("*.txt") + self.file_manager.list_files("*.md")
        
        if not files:
            print("\nNo files to correct")
            return
        
        print("\nFiles:")
        for i, filepath in enumerate(files, 1):
            print(f"{i}. {filepath.name}")
        
        selection = input("\nEnter file numbers (e.g., 1 3 5) or 'all': ").strip()
        
        if selection.lower() == 'all':
            files_to_correct = files
        else:
            try:
                indices = [int(x) - 1 for x in selection.split()]
                files_to_correct = [files[i] for i in indices if 0 <= i < len(files)]
            except ValueError:
                print("Invalid input")
                return
        
        if not files_to_correct:
            print("No valid files selected")
            return
        
        self.correction_manager.batch_correct(files_to_correct, show_live=False)
    
    def _interactive_correction(self) -> None:
        """Interactive correction with options."""
        files = self.file_manager.list_files("*.txt") + self.file_manager.list_files("*.md")
        
        if not files:
            print("\nNo files to correct")
            return
        
        print("\nFiles:")
        for i, filepath in enumerate(files, 1):
            print(f"{i}. {filepath.name}")
        
        try:
            choice = int(input(f"\nSelect file (1-{len(files)}, 0 to cancel): ").strip())
            if choice == 0:
                return
            
            if 1 <= choice <= len(files):
                filepath = files[choice - 1]
                self.correction_manager.interactive_correct(filepath)
        except ValueError:
            print("Invalid input")
    
    def _handle_exit(self) -> None:
        """Handle application exit."""
        print("\n" + "="*60)
        
        # Stop Ollama if configured
        if self.config.get('ai', {}).get('auto_stop_ollama', False):
            self.correction_manager.ollama.stop()
        
        print("Thank you for using Vosk Speech-to-Text!")
        print("="*60)
        logger.info("User exited application")
