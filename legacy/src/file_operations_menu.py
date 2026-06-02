"""
File operations menu - no models required.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from file_manager import FileManager
from utils import format_file_size

logger = logging.getLogger("vosk_stt.fileops")

class FileOperationsMenu:
    """File operations without requiring Vosk or Ollama."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.file_manager = FileManager(config['output']['folder'])
        logger.info("FileOperationsMenu initialized")
    
    def show(self) -> None:
        """Display file operations menu."""
        while True:
            print("\n" + "="*60)
            print("FILE OPERATIONS")
            print("="*60)
            print("1. View All Files")
            print("2. View File Details")
            print("3. Search Files")
            print("4. Delete File")
            print("5. Merge Files")
            print("6. File Statistics")
            print("7. Export File List")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._view_all_files()
            elif choice == '2':
                self._view_file_details()
            elif choice == '3':
                self._search_files()
            elif choice == '4':
                self._delete_file()
            elif choice == '5':
                self._merge_files()
            elif choice == '6':
                self._file_statistics()
            elif choice == '7':
                self._export_file_list()
            else:
                print("Invalid choice")
    
    def _view_all_files(self) -> None:
        """Display all files with basic info."""
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
            print(f"   Modified: {info['modified'].strftime('%Y-%m-%d %H:%M')}")
        
        print("="*60)
    
    def _view_file_details(self) -> None:
        """View detailed information about a specific file."""
        files = self._get_files()
        if not files:
            return
        
        filepath = self._select_file(files, "View details for")
        if not filepath:
            return
        
        info = self.file_manager.get_file_info(filepath)
        content = self.file_manager.read_file(filepath)
        
        print("\n" + "="*60)
        print("FILE DETAILS")
        print("="*60)
        print(f"Name: {info['name']}")
        print(f"Path: {info['path']}")
        print(f"Size: {format_file_size(info['size'])}")
        print(f"Words: {info['word_count']:,}")
        print(f"Characters: {info['char_count']:,}")
        print(f"Modified: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if content:
            print("\n--- PREVIEW (first 300 characters) ---")
            print(content[:300])
            if len(content) > 300:
                print("...")
        
        print("="*60)
        
        # Options
        print("\n1. View full content")
        print("2. Copy to clipboard (if available)")
        print("0. Back")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1' and content:
            print("\n" + "="*60)
            print("FULL CONTENT")
            print("="*60)
            print(content)
            print("="*60)
    
    def _search_files(self) -> None:
        """Search for text in files."""
        search_term = input("\nEnter search term: ").strip()
        
        if not search_term:
            return
        
        case_sensitive = input("Case sensitive? (yes/no, default no): ").strip().lower() == 'yes'
        
        results = self.file_manager.search_files(search_term, case_sensitive)
        
        if not results:
            print(f"\n'{search_term}' not found in any files")
            return
        
        print(f"\n" + "="*60)
        print(f"SEARCH RESULTS: '{search_term}'")
        print(f"Found in {len(results)} file(s)")
        print("="*60)
        
        for filepath, context in results:
            print(f"\n• {filepath.name}")
            print(f"  ...{context}...")
        
        print("="*60)
    
    def _delete_file(self) -> None:
        """Delete a file."""
        files = self._get_files()
        if not files:
            return
        
        filepath = self._select_file(files, "Delete")
        if not filepath:
            return
        
        # Show file info before deleting
        info = self.file_manager.get_file_info(filepath)
        print(f"\nFile: {info['name']}")
        print(f"Size: {format_file_size(info['size'])}")
        print(f"Words: {info['word_count']:,}")
        
        confirm = input(f"\n⚠ Delete '{filepath.name}'? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            if self.file_manager.delete_file(filepath):
                print(f"✓ Deleted: {filepath.name}")
            else:
                print("✗ Failed to delete")
        else:
            print("Delete cancelled")
    
    def _merge_files(self) -> None:
        """Merge multiple files."""
        files = self._get_files()
        
        if len(files) < 2:
            print("\nNeed at least 2 files to merge")
            return
        
        print("\nAvailable files:")
        for i, filepath in enumerate(files, 1):
            info = self.file_manager.get_file_info(filepath)
            print(f"{i}. {filepath.name} ({info['word_count']:,} words)")
        
        selection = input("\nEnter file numbers to merge (e.g., 1 3 5): ").strip()
        
        try:
            indices = [int(x) - 1 for x in selection.split()]
            files_to_merge = [files[i] for i in indices if 0 <= i < len(files)]
            
            if not files_to_merge:
                print("No valid files selected")
                return
            
            # Ask for output name
            output_name = input("\nEnter name for merged file (or Enter for default): ").strip()
            if output_name and not output_name.endswith('.txt'):
                output_name += '.txt'
            
            merged_path = self.file_manager.merge_files(files_to_merge, output_name)
            
            if merged_path:
                print(f"\n✓ Files merged into: {merged_path.name}")
                merged_info = self.file_manager.get_file_info(merged_path)
                print(f"Total words: {merged_info['word_count']:,}")
            else:
                print("✗ Merge failed")
        
        except ValueError:
            print("Invalid input")
    
    def _file_statistics(self) -> None:
        """Show comprehensive file statistics."""
        files = self.file_manager.list_files()
        
        if not files:
            print("\nNo files to analyze")
            return
        
        # Calculate statistics
        total_size = 0
        total_words = 0
        total_chars = 0
        oldest = None
        newest = None
        
        for filepath in files:
            info = self.file_manager.get_file_info(filepath)
            total_size += info['size']
            total_words += info['word_count']
            total_chars += info['char_count']
            
            if oldest is None or info['modified'] < oldest:
                oldest = info['modified']
            if newest is None or info['modified'] > newest:
                newest = info['modified']
        
        avg_words = total_words // len(files) if files else 0
        
        print("\n" + "="*60)
        print("FILE STATISTICS")
        print("="*60)
        print(f"Total Files: {len(files)}")
        print(f"Total Size: {format_file_size(total_size)}")
        print(f"Total Words: {total_words:,}")
        print(f"Total Characters: {total_chars:,}")
        print(f"Average Words per File: {avg_words:,}")
        print(f"Oldest File: {oldest.strftime('%Y-%m-%d %H:%M') if oldest else 'N/A'}")
        print(f"Newest File: {newest.strftime('%Y-%m-%d %H:%M') if newest else 'N/A'}")
        print("="*60)
        
        # File type breakdown
        txt_files = len([f for f in files if f.suffix == '.txt'])
        md_files = len([f for f in files if f.suffix == '.md'])
        
        print("\nFile Types:")
        print(f"  .txt files: {txt_files}")
        print(f"  .md files: {md_files}")
        print("="*60)
    
    def _export_file_list(self) -> None:
        """Export file list to a text file."""
        files = self._get_files()
        if not files:
            return
        
        output_name = input("\nEnter export filename (default: file_list.txt): ").strip()
        if not output_name:
            output_name = "file_list.txt"
        elif not output_name.endswith('.txt'):
            output_name += '.txt'
        
        output_path = self.file_manager.output_folder / output_name
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("TRANSCRIPTION FILES\n")
                f.write("="*60 + "\n\n")
                
                for i, filepath in enumerate(files, 1):
                    info = self.file_manager.get_file_info(filepath)
                    f.write(f"{i}. {info['name']}\n")
                    f.write(f"   Size: {format_file_size(info['size'])}\n")
                    f.write(f"   Words: {info['word_count']:,}\n")
                    f.write(f"   Modified: {info['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("\n")
            
            print(f"\n✓ File list exported to: {output_name}")
        
        except Exception as e:
            print(f"\n✗ Export failed: {e}")
    
    def _get_files(self):
        """Get list of files, show message if none."""
        files = self.file_manager.list_files()
        if not files:
            print("\nNo files found")
        return files
    
    def _select_file(self, files, action="Select"):
        """Helper to select a file from list."""
        print(f"\n{action} file:")
        for i, f in enumerate(files, 1):
            info = self.file_manager.get_file_info(f)
            print(f"{i}. {f.name} ({format_file_size(info['size'])})")
        
        try:
            choice = int(input(f"\nFile (1-{len(files)}, 0=cancel): ").strip())
            if choice == 0:
                return None
            if 1 <= choice <= len(files):
                return files[choice - 1]
        except ValueError:
            print("Invalid input")
        return None
