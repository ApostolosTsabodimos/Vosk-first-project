"""
Keyboard shortcuts and quick navigation.
"""

import logging

logger = logging.getLogger("vosk_stt.shortcuts")

class ShortcutHandler:
    """Handle keyboard shortcuts for quick navigation."""
    
    # Shortcut mappings
    SHORTCUTS = {
        # Main menu
        't': ('1', 'Transcribe Only'),
        'c': ('2', 'Correct Only'),
        'f': ('3', 'Full Workflow'),
        'o': ('4', 'File Operations'),
        's': ('5', 'Settings & Tools'),
        'v': ('6', 'View Options Tree'),
        'm': ('7', 'Check Memory'),
        'q': ('0', 'Exit'),
        'x': ('0', 'Exit'),
        
        # Common actions
        'h': ('help', 'Show Help'),
        '?': ('help', 'Show Help'),
        'r': ('recent', 'Recent Files'),
    }
    
    @staticmethod
    def show_shortcuts_help():
        """Display all available shortcuts."""
        print("\n" + "="*60)
        print("KEYBOARD SHORTCUTS")
        print("="*60)
        print("\nMain Menu:")
        print("  T - Transcribe Only")
        print("  C - Correct Only")
        print("  F - Full Workflow")
        print("  O - File Operations")
        print("  S - Settings & Tools")
        print("  V - View Options Tree")
        print("  M - Check Memory")
        print("  Q/X - Exit")
        print("\nQuick Actions:")
        print("  R - Recent Files")
        print("  H/? - This Help")
        print("\nGeneral:")
        print("  0 - Back / Cancel")
        print("  Ctrl+C - Stop / Interrupt")
        print("  Ctrl+D - EOF (in text input)")
        print("="*60)
    
    @staticmethod
    def parse_input(user_input: str) -> str:
        """
        Parse user input and translate shortcuts to menu numbers.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Translated input (number or command)
        """
        user_input = user_input.strip().lower()
        
        # Check if it's a shortcut
        if user_input in ShortcutHandler.SHORTCUTS:
            translated, description = ShortcutHandler.SHORTCUTS[user_input]
            logger.debug(f"Shortcut '{user_input}' → {description}")
            return translated
        
        # Return as-is if not a shortcut
        return user_input
    
    @staticmethod
    def get_input_with_shortcuts(prompt: str = "Choice: ") -> str:
        """
        Get user input with shortcut support.
        
        Args:
            prompt: Input prompt to display
            
        Returns:
            Translated user choice
        """
        user_input = input(f"{prompt}").strip()
        
        # Handle help
        if user_input.lower() in ['h', '?', 'help']:
            ShortcutHandler.show_shortcuts_help()
            return ShortcutHandler.get_input_with_shortcuts(prompt)
        
        return ShortcutHandler.parse_input(user_input)


def show_quick_actions_bar():
    """Display quick actions bar at top of menus."""
    print("─" * 60)
    print("Quick: [T]ranscribe | [C]orrect | [F]ile ops | [R]ecent | [H]elp")
    print("─" * 60)
