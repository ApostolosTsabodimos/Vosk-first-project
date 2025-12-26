#!/usr/bin/env python3
"""
Vosk Speech-to-Text - Optimized Edition
Three operating modes for optimal resource usage.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils import setup_logging, load_config, check_available_memory
from ui_modes import show_mode_selection, TranscribeOnlyMode, CorrectOnlyMode, FullWorkflowMode
from settings_menu import SettingsMenu
from file_operations_menu import FileOperationsMenu
from options_tree import show_options_tree

def show_memory_status():
    """Display current memory status."""
    from utils import check_available_memory, format_file_size
    
    mem = check_available_memory()
    print("\n" + "="*60)
    print("SYSTEM MEMORY STATUS")
    print("="*60)
    print(f"Available RAM: {mem['available']:.1f} GB / {mem['total']:.1f} GB")
    print(f"Swap Space: {mem['swap_free']:.1f} GB / {mem['swap_total']:.1f} GB")
    
    # Recommendations
    if mem['swap_total'] < 4.0:
        print("\n⚠ Recommendation: Add swap space for large models")
        print("  sudo fallocate -l 8G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile")
    
    print("="*60)

def main():
    """Main application entry point."""
    logger = setup_logging()
    logger.info("Starting Vosk Speech-to-Text Application")
    
    try:
        # Load configuration
        config = load_config()
        
        # Show welcome and memory status
        print("\n" + "="*60)
        print("VOSK SPEECH-TO-TEXT - OPTIMIZED EDITION")
        print("="*60)
        
        show_memory_status()
        
        # Main loop
        while True:
            mode_choice = show_mode_selection()
            
            if mode_choice == '0':
                print("\nExiting...")
                break
            
            elif mode_choice == '1':
                # TRANSCRIBE ONLY MODE
                print("\n" + "="*60)
                print("MODE 1: TRANSCRIPTION ONLY")
                print("Resources: Vosk Model (~6-8GB)")
                print("Ollama: Will remain OFF")
                print("="*60)
                
                mode = TranscribeOnlyMode(config)
                mode.run()
                mode.cleanup()
            
            elif mode_choice == '2':
                # CORRECT ONLY MODE
                print("\n" + "="*60)
                print("MODE 2: CORRECTION ONLY")
                print("Resources: Ollama (~4-5GB)")
                print("Vosk: Will remain OFF")
                print("="*60)
                
                mode = CorrectOnlyMode(config)
                mode.run()
                mode.cleanup()
            
            elif mode_choice == '3':
                # FULL WORKFLOW MODE
                print("\n" + "="*60)
                print("MODE 3: FULL WORKFLOW (OPTIMIZED)")
                print("Process: Transcribe → Unload Vosk → Load Ollama → Correct")
                print("Max Memory: ~6-8GB (sequential, not parallel)")
                print("="*60)
                
                mode = FullWorkflowMode(config)
                mode.run()
                mode.cleanup()
            
            elif mode_choice == '4':
                # FILE OPERATIONS
                print("\n" + "="*60)
                print("MODE 4: FILE OPERATIONS")
                print("No models loaded - minimal memory usage")
                print("="*60)
                
                file_ops = FileOperationsMenu(config)
                file_ops.show()
            
            elif mode_choice == '5':
                # SETTINGS & TOOLS
                settings = SettingsMenu(config)
                settings.show()
            
            elif mode_choice == '6':
                # VIEW OPTIONS TREE
                show_options_tree()
            
            elif mode_choice == '7':
                # Show memory status
                show_memory_status()
            
            else:
                print("Invalid choice")
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n\nExiting...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
