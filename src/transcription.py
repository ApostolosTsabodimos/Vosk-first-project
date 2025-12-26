"""
Audio transcription using Vosk speech recognition.
"""

import json
import logging
import pyaudio
import threading
import time
from pathlib import Path
from typing import List, Optional, Callable
from vosk import Model, KaldiRecognizer

logger = logging.getLogger("vosk_stt.transcription")

class AutoSaver:
    """Automatically save transcription at intervals."""
    
    def __init__(self, interval: int, save_callback: Callable):
        """
        Initialize auto-saver.
        
        Args:
            interval: Save interval in seconds
            save_callback: Function to call for saving
        """
        self.interval = interval
        self.save_callback = save_callback
        self.running = False
        self.thread = None
        logger.debug(f"AutoSaver initialized with {interval}s interval")
    
    def start(self) -> None:
        """Start auto-saving."""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("AutoSaver started")
    
    def stop(self) -> None:
        """Stop auto-saving."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("AutoSaver stopped")
    
    def _run(self) -> None:
        """Auto-save loop."""
        while self.running:
            time.sleep(self.interval)
            if self.running:
                try:
                    self.save_callback()
                    timestamp = time.strftime('%H:%M:%S')
                    print(f"\n[Auto-saved at {timestamp}]")
                    logger.debug(f"Auto-save triggered at {timestamp}")
                except Exception as e:
                    logger.error(f"Auto-save failed: {e}")

class VoskTranscriber:
    """Handles audio recording and transcription with Vosk."""
    
    def __init__(
        self,
        model_path: str,
        sample_rate: int = 16000,
        buffer_size: int = 8192
    ):
        """
        Initialize transcriber.
        
        Args:
            model_path: Path to Vosk model
            sample_rate: Audio sample rate
            buffer_size: Audio buffer size
        """
        self.model_path = Path(model_path)
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.model = None
        self.recognizer = None
        self.transcription: List[str] = []
        
        logger.info(f"VoskTranscriber initialized with model: {model_path}")
    
    def load_model(self) -> bool:
        """
        Load Vosk model.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.model_path.exists():
            logger.error(f"Model not found at {self.model_path}")
            return False
        
        try:
            logger.info("Loading Vosk model...")
            print("\nLoading Vosk model (this may take a moment)...")
            
            self.model = Model(str(self.model_path))
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            
            logger.info("Model loaded successfully")
            print("✓ Model loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            print(f"✗ Failed to load model: {e}")
            return False
    
    def get_default_device(self) -> Optional[dict]:
        """
        Get default audio input device.
        
        Returns:
            Device info dictionary, or None if failed
        """
        try:
            audio = pyaudio.PyAudio()
            device_info = audio.get_default_input_device_info()
            audio.terminate()
            logger.info(f"Default device: {device_info['name']}")
            return device_info
        except Exception as e:
            logger.error(f"Failed to get default device: {e}")
            return None
    
    def transcribe(
        self,
        auto_save_interval: Optional[int] = None,
        save_callback: Optional[Callable] = None
    ) -> List[str]:
        """
        Start transcription session.
        
        Args:
            auto_save_interval: Auto-save interval in seconds (None to disable)
            save_callback: Callback for auto-saving
            
        Returns:
            List of transcribed text segments
        """
        if not self.model:
            logger.error("Model not loaded")
            return []
        
        # Reset transcription
        self.transcription = []
        
        # Setup audio stream
        audio = pyaudio.PyAudio()
        device_info = audio.get_default_input_device_info()
        
        print(f"Using microphone: {device_info['name']}")
        logger.info(f"Starting transcription with device: {device_info['name']}")
        
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.buffer_size,
            input_device_index=device_info['index']
        )
        stream.start_stream()
        
        # Setup auto-saver
        auto_saver = None
        if auto_save_interval and save_callback:
            auto_saver = AutoSaver(auto_save_interval, save_callback)
            auto_saver.start()
        
        print("\n" + "="*60)
        print("RECORDING - Speak naturally at your normal pace")
        print("Press Ctrl+C to stop and save")
        if auto_saver:
            print(f"Auto-save: Every {auto_save_interval // 60} minutes")
        print("="*60 + "\n")
        
        try:
            while True:
                data = stream.read(self.buffer_size, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        print(f"✓ {text}")
                        self.transcription.append(text)
                        logger.debug(f"Recognized: {text}")
                else:
                    # Show partial results
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '').strip()
                    
                    if partial_text:
                        print(f"  → {partial_text}...", end='\r', flush=True)
        
        except KeyboardInterrupt:
            logger.info("Transcription interrupted by user")
            print("\n\n" + "="*60)
            print("STOPPING")
            print("="*60)
            
            # Stop auto-saver
            if auto_saver:
                auto_saver.stop()
            
            # Get final result
            final = json.loads(self.recognizer.FinalResult())
            final_text = final.get('text', '').strip()
            
            if final_text:
                print(f"✓ {final_text}")
                self.transcription.append(final_text)
                logger.debug(f"Final: {final_text}")
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            logger.info(f"Transcription complete: {len(self.transcription)} segments")
            return self.transcription
        
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            if auto_saver:
                auto_saver.stop()
            stream.stop_stream()
            stream.close()
            audio.terminate()
            raise
    
    def get_full_text(self) -> str:
        """
        Get full transcription as single string.
        
        Returns:
            Complete transcription text
        """
        return ' '.join(self.transcription)
    
    def get_word_count(self) -> int:
        """
        Get total word count.
        
        Returns:
            Number of words transcribed
        """
        return len(self.get_full_text().split())
