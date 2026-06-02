"""
Settings and tools menu for configuration and diagnostics.
"""

import logging
import subprocess
import yaml
from pathlib import Path
from typing import Dict, Any
from utils import check_available_memory, format_file_size, get_project_root
from cache_manager import get_cache

logger = logging.getLogger("vosk_stt.settings")

class SettingsMenu:
    """Settings and diagnostic tools."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = get_cache()
        logger.info("SettingsMenu initialized")
    
    def show(self) -> None:
        """Display settings menu."""
        while True:
            print("\n" + "="*60)
            print("SETTINGS & TOOLS")
            print("="*60)
            print("1. View Configuration")
            print("2. Edit Configuration")
            print("3. Check Memory Status")
            print("4. Test Microphone")
            print("5. Ollama Model Management")
            print("6. Cache Management")
            print("7. View Logs")
            print("8. System Diagnostics")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._view_config()
            elif choice == '2':
                self._edit_config()
            elif choice == '3':
                self._check_memory()
            elif choice == '4':
                self._test_microphone()
            elif choice == '5':
                self._ollama_management()
            elif choice == '6':
                self._cache_management()
            elif choice == '7':
                self._view_logs()
            elif choice == '8':
                self._system_diagnostics()
            else:
                print("Invalid choice")
    
    def _view_config(self) -> None:
        """Display current configuration."""
        print("\n" + "="*60)
        print("CURRENT CONFIGURATION")
        print("="*60)
        
        print("\n[Vosk Model]")
        print(f"  Path: {self.config['vosk']['model_path']}")
        print(f"  Sample Rate: {self.config['vosk']['sample_rate']} Hz")
        print(f"  Buffer Size: {self.config['vosk']['buffer_size']}")
        
        print("\n[Output]")
        print(f"  Folder: {self.config['output']['folder']}")
        print(f"  Default Format: {self.config['output']['default_format']}")
        print(f"  Auto-save Interval: {self.config['output']['auto_save_interval']}s")
        
        print("\n[AI Correction]")
        print(f"  Model: {self.config['ai']['model']}")
        print(f"  Temperature: {self.config['ai']['temperature']}")
        print(f"  Show Live: {self.config['ai']['show_live']}")
        print(f"  Auto-start Ollama: {self.config['ai']['auto_start_ollama']}")
        
        print("="*60)
    
    def _edit_config(self) -> None:
        """Open config file for editing."""
        config_path = get_project_root() / "config.yaml"
        
        print("\nOpening config file in editor...")
        print(f"Path: {config_path}")
        
        editors = ['nano', 'vim', 'kate', 'gedit']
        for editor in editors:
            try:
                subprocess.run([editor, str(config_path)], check=True)
                print("\n✓ Configuration saved")
                print("⚠ Restart the application for changes to take effect")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        print("\n✗ No text editor found")
        print(f"Please edit manually: {config_path}")
    
    def _check_memory(self) -> None:
        """Check system memory status."""
        mem = check_available_memory()
        
        print("\n" + "="*60)
        print("MEMORY STATUS")
        print("="*60)
        print(f"Total RAM: {mem['total']:.2f} GB")
        print(f"Available RAM: {mem['available']:.2f} GB")
        print(f"Free RAM: {mem['free']:.2f} GB")
        print(f"Total Swap: {mem['swap_total']:.2f} GB")
        print(f"Free Swap: {mem['swap_free']:.2f} GB")
        
        print("\n[Recommendations]")
        
        if mem['available'] < 6.0:
            print("  ⚠ Low memory - large models may struggle")
            print("  → Close other applications")
            print("  → Use Mode 1 (Transcribe) or Mode 2 (Correct) separately")
        else:
            print("  ✓ Sufficient memory for all operations")
        
        if mem['swap_total'] < 4.0:
            print("\n  ⚠ No/low swap space")
            print("  → Add swap: sudo fallocate -l 8G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile")
        else:
            print(f"\n  ✓ Swap space available: {mem['swap_total']:.1f} GB")
        
        print("="*60)
    
    def _test_microphone(self) -> None:
        """Test microphone recording."""
        print("\n" + "="*60)
        print("MICROPHONE TEST")
        print("="*60)
        
        try:
            import pyaudio
            
            audio = pyaudio.PyAudio()
            device_info = audio.get_default_input_device_info()
            
            print(f"\nDefault Microphone:")
            print(f"  Name: {device_info['name']}")
            print(f"  Index: {device_info['index']}")
            print(f"  Sample Rate: {device_info['defaultSampleRate']} Hz")
            print(f"  Channels: {device_info['maxInputChannels']}")
            
            print("\nTesting recording for 3 seconds...")
            print("Speak into your microphone...")
            
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
                input_device_index=device_info['index']
            )
            
            # Record for 3 seconds
            frames = []
            for _ in range(0, int(16000 / 1024 * 3)):
                data = stream.read(1024)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            print("\n✓ Microphone test successful")
            print("  Your microphone is working correctly")
            
        except Exception as e:
            print(f"\n✗ Microphone test failed: {e}")
            print("\nTroubleshooting:")
            print("  1. Check microphone is connected")
            print("  2. Check permissions: alsamixer")
            print("  3. Test with: arecord -d 3 test.wav && aplay test.wav")
    
    def _ollama_management(self) -> None:
        """Manage Ollama models."""
        print("\n" + "="*60)
        print("OLLAMA MODEL MANAGEMENT")
        print("="*60)
        
        try:
            # Check if Ollama is installed
            result = subprocess.run(['which', 'ollama'], capture_output=True)
            if result.returncode != 0:
                print("\n✗ Ollama not found")
                print("Install: sudo pacman -S ollama")
                return
            
            # List models
            print("\n1. List installed models")
            print("2. Pull/download new model")
            print("3. Remove model")
            print("4. Check Ollama service status")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                print("\nInstalled models:")
                subprocess.run(['ollama', 'list'])
            
            elif choice == '2':
                print("\nAvailable models:")
                print("  mistral (4GB) - Recommended")
                print("  llama3.2 (2GB) - Smaller")
                print("  llama3.1 (5GB) - Larger, more accurate")
                model = input("\nModel name to download: ").strip()
                if model:
                    subprocess.run(['ollama', 'pull', model])
            
            elif choice == '3':
                subprocess.run(['ollama', 'list'])
                model = input("\nModel name to remove: ").strip()
                if model:
                    subprocess.run(['ollama', 'rm', model])
            
            elif choice == '4':
                subprocess.run(['systemctl', 'status', 'ollama'])
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    def _cache_management(self) -> None:
        """Manage caching system."""
        while True:
            print("\n" + "="*60)
            print("CACHE MANAGEMENT")
            print("="*60)
            print("1. View cache statistics")
            print("2. Clear file cache")
            print("3. Clear correction cache")
            print("4. Clear all caches")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.cache.print_stats()
            elif choice == '2':
                self.cache.file_cache.clear()
                print("\n✓ File cache cleared")
            elif choice == '3':
                self.cache.correction_cache.clear()
                print("\n✓ Correction cache cleared")
            elif choice == '4':
                self.cache.clear_all()
                print("\n✓ All caches cleared")
    
    def _view_logs(self) -> None:
        """View application logs."""
        log_dir = get_project_root() / "logs"
        log_file = log_dir / "vosk_stt.log"
        
        if not log_file.exists():
            print("\n✗ No log file found")
            return
        
        print("\n" + "="*60)
        print("APPLICATION LOGS")
        print("="*60)
        print(f"Log file: {log_file}")
        print(f"Size: {format_file_size(log_file.stat().st_size)}")
        print("\n1. View recent logs (last 50 lines)")
        print("2. View all logs")
        print("3. Search logs")
        print("4. Clear logs")
        print("0. Back")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            subprocess.run(['tail', '-n', '50', str(log_file)])
        elif choice == '2':
            subprocess.run(['less', str(log_file)])
        elif choice == '3':
            term = input("Search term: ").strip()
            if term:
                subprocess.run(['grep', term, str(log_file)])
        elif choice == '4':
            confirm = input("Clear logs? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                log_file.write_text("")
                print("✓ Logs cleared")
    
    def _system_diagnostics(self) -> None:
        """Run system diagnostics."""
        print("\n" + "="*60)
        print("SYSTEM DIAGNOSTICS")
        print("="*60)
        
        # Python version
        import sys
        print(f"\nPython: {sys.version.split()[0]}")
        
        # Installed packages
        try:
            import vosk
            print(f"Vosk: {vosk.__version__ if hasattr(vosk, '__version__') else 'installed'}")
        except ImportError:
            print("Vosk: NOT INSTALLED")
        
        try:
            import pyaudio
            print("PyAudio: installed")
        except ImportError:
            print("PyAudio: NOT INSTALLED")
        
        try:
            import ollama
            print("Ollama: installed")
        except ImportError:
            print("Ollama: NOT INSTALLED")
        
        # Vosk model
        model_path = Path(self.config['vosk']['model_path'])
        if model_path.exists():
            size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            print(f"\nVosk Model: {format_file_size(size)}")
        else:
            print(f"\nVosk Model: NOT FOUND at {model_path}")
        
        # Output folder
        output_folder = Path(self.config['output']['folder'])
        if output_folder.exists():
            files = list(output_folder.glob('*'))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            print(f"\nTranscription Files: {len(files)} files, {format_file_size(total_size)}")
        else:
            print(f"\nTranscription Folder: NOT FOUND")
        
        # Memory
        mem = check_available_memory()
        print(f"\nAvailable Memory: {mem['available']:.1f} GB / {mem['total']:.1f} GB")
        
        # Cache stats
        stats = self.cache.get_stats()
        print(f"\nCache Hit Rate: {stats['hit_rate']}")
        
        print("="*60)
