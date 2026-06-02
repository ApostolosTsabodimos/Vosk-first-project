"""
Ollama service management and AI model interaction.
"""

import subprocess
import time
import logging
from typing import Optional, Iterator

logger = logging.getLogger("vosk_stt.ollama")

class OllamaManager:
    """Manages Ollama service and model interactions."""
    
    def __init__(self, model: str = "mistral", auto_start: bool = True):
        """
        Initialize Ollama manager.
        
        Args:
            model: Model name to use
            auto_start: Automatically start service if not running
        """
        self.model = model
        self.auto_start = auto_start
        logger.info(f"Initialized OllamaManager with model: {model}")
    
    def is_running(self) -> bool:
        """
        Check if Ollama service is running.
        
        Returns:
            True if running, False otherwise
        """
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'ollama'],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_active = result.stdout.strip() == 'active'
            logger.debug(f"Ollama service active: {is_active}")
            return is_active
        except Exception as e:
            logger.error(f"Error checking Ollama status: {e}")
            return False
    
    def start(self) -> bool:
        """
        Start Ollama service.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running():
            logger.info("Ollama already running")
            return True
        
        logger.info("Starting Ollama service...")
        print("\nStarting Ollama service...")
        
        try:
            subprocess.run(
                ['sudo', 'systemctl', 'start', 'ollama'],
                check=True,
                timeout=10
            )
            time.sleep(2)  # Give it time to start
            
            if self.is_running():
                logger.info("Ollama started successfully")
                print("✓ Ollama started")
                return True
            else:
                logger.error("Ollama failed to start")
                print("✗ Ollama failed to start")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Ollama: {e}")
            print("✗ Failed to start Ollama. Please run: sudo systemctl start ollama")
            return False
        except Exception as e:
            logger.error(f"Unexpected error starting Ollama: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop Ollama service.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_running():
            logger.info("Ollama already stopped")
            return True
        
        logger.info("Stopping Ollama service...")
        print("\nStopping Ollama service...")
        
        try:
            subprocess.run(
                ['sudo', 'systemctl', 'stop', 'ollama'],
                check=True,
                timeout=10
            )
            logger.info("Ollama stopped successfully")
            print("✓ Ollama stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop Ollama: {e}")
            print("✗ Failed to stop Ollama")
            return False
    
    def ensure_running(self) -> bool:
        """
        Ensure Ollama is running, starting it if necessary.
        
        Returns:
            True if running, False if failed to start
        """
        if self.is_running():
            return True
        
        if self.auto_start:
            return self.start()
        
        return False
    
    def correct_text(
        self,
        text: str,
        temperature: float = 0.3,
        prompt_template: Optional[str] = None,
        stream: bool = True
    ) -> Optional[str]:
        """
        Correct text using AI model.
        
        Args:
            text: Text to correct
            temperature: Model temperature (0.0-2.0)
            prompt_template: Custom prompt template with {text} placeholder
            stream: Stream response in real-time
            
        Returns:
            Corrected text, or None if failed
        """
        if not self.ensure_running():
            logger.error("Ollama not running, cannot correct text")
            return None
        
        try:
            import ollama
            
            # Use custom prompt or default
            if prompt_template is None:
                prompt = f"""This is a speech-to-text transcription that may contain errors.
Please correct any mistakes while preserving the original meaning and style.

Text to correct:
{text}

Corrected text:"""
            else:
                prompt = prompt_template.format(text=text)
            
            logger.info(f"Sending {len(text)} chars to {self.model} for correction")
            
            if stream:
                return self._correct_with_stream(prompt, temperature)
            else:
                return self._correct_without_stream(prompt, temperature)
                
        except ImportError:
            logger.error("ollama package not installed")
            print("\n✗ Error: ollama package not installed")
            print("Run: pip install ollama")
            return None
        except Exception as e:
            logger.error(f"Error during correction: {e}", exc_info=True)
            print(f"\n✗ Error during correction: {e}")
            return None
    
    def _correct_with_stream(self, prompt: str, temperature: float) -> str:
        """Correct text with streaming output."""
        import ollama
        
        print("\n" + "="*60)
        print("🤖 MISTRAL AI PROCESSING (LIVE)")
        print("="*60)
        print()
        
        full_response = ""
        
        for chunk in ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': temperature},
            stream=True
        ):
            content = chunk['message']['content']
            print(content, end='', flush=True)
            full_response += content
        
        print("\n" + "="*60)
        logger.info(f"Correction complete: {len(full_response)} chars")
        return full_response.strip()
    
    def _correct_without_stream(self, prompt: str, temperature: float) -> str:
        """Correct text without streaming."""
        import ollama
        
        print("\n🤖 Processing with Mistral AI...")
        
        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': temperature}
        )
        
        result = response['message']['content'].strip()
        logger.info(f"Correction complete: {len(result)} chars")
        return result
    
    def list_models(self) -> list:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            import ollama
            models = ollama.list()
            model_names = [m['name'] for m in models.get('models', [])]
            logger.info(f"Available models: {model_names}")
            return model_names
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
