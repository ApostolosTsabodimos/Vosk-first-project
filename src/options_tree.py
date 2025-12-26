"""
Display complete options tree for the application.
"""

def show_options_tree():
    """Display the complete options tree."""
    tree = """
╔══════════════════════════════════════════════════════════════╗
║         VOSK SPEECH-TO-TEXT - COMPLETE OPTIONS TREE          ║
╚══════════════════════════════════════════════════════════════╝

MAIN MENU
│
├─ 1. TRANSCRIBE ONLY MODE (Vosk ON, Ollama OFF, ~6-8GB RAM)
│   │
│   ├─ 1. Quick Transcription
│   │   └─ Record with default settings → Save with timestamp
│   │
│   ├─ 2. Custom Filename Transcription
│   │   ├─ Enter custom filename
│   │   ├─ Select format:
│   │   │   ├─ Plain text (.txt)
│   │   │   ├─ Markdown (.md)
│   │   │   └─ Timestamped (.txt with time markers)
│   │   └─ Record → Save
│   │
│   ├─ 3. Append to Existing File
│   │   ├─ View existing files
│   │   ├─ Select file to append to
│   │   └─ Record → Append to selected file
│   │
│   └─ 0. Back to Main Menu
│
├─ 2. CORRECT ONLY MODE (Vosk OFF, Ollama ON, ~4-5GB RAM)
│   │
│   ├─ 1. Interactive Correction
│   │   ├─ Select file
│   │   ├─ Choose correction style:
│   │   │   ├─ Live processing (watch AI work)
│   │   │   ├─ Silent processing (faster)
│   │   │   ├─ Custom prompt (your instructions)
│   │   │   └─ Adjust temperature (0.0-2.0)
│   │   ├─ AI processes text
│   │   ├─ View differences (before/after)
│   │   ├─ Preview corrected text
│   │   └─ Save corrected version
│   │
│   ├─ 2. Quick Correction
│   │   ├─ Select file
│   │   ├─ Process with default settings
│   │   └─ Save corrected version
│   │
│   ├─ 3. Batch Correct Multiple Files
│   │   ├─ Select files (or 'all')
│   │   ├─ Process all silently
│   │   └─ View summary report
│   │
│   └─ 0. Back to Main Menu
│
├─ 3. FULL WORKFLOW MODE (Sequential: Vosk → Ollama, ~6-8GB max)
│   │
│   ├─ Enter filename (or use default timestamp)
│   │
│   ├─ STEP 1: Transcription
│   │   ├─ Load Vosk model
│   │   ├─ Record audio from microphone
│   │   ├─ Save transcription
│   │   └─ Unload Vosk, free memory
│   │
│   ├─ STEP 2: Memory Cleanup
│   │   └─ Force garbage collection
│   │
│   ├─ STEP 3: AI Correction
│   │   ├─ Load Ollama
│   │   ├─ Correct transcription
│   │   ├─ View differences
│   │   └─ Save corrected version
│   │
│   └─ Complete & Cleanup
│
├─ 4. FILE OPERATIONS (No models needed, minimal RAM)
│   │
│   ├─ 1. View All Files
│   │   └─ List all files with size, word count, date
│   │
│   ├─ 2. View File Details
│   │   ├─ Select file
│   │   ├─ View metadata and statistics
│   │   ├─ Preview content (first 300 chars)
│   │   └─ Option to view full content
│   │
│   ├─ 3. Search Files
│   │   ├─ Enter search term
│   │   ├─ Optional: case sensitive search
│   │   └─ View matches with context
│   │
│   ├─ 4. Delete File
│   │   ├─ Select file
│   │   ├─ View file details
│   │   ├─ Confirm deletion
│   │   └─ Delete permanently
│   │
│   ├─ 5. Merge Files
│   │   ├─ Select multiple files
│   │   ├─ Enter name for merged file
│   │   └─ Create merged file with source markers
│   │
│   ├─ 6. File Statistics
│   │   ├─ Total files, size, words
│   │   ├─ Average words per file
│   │   ├─ Oldest/newest files
│   │   └─ File type breakdown
│   │
│   ├─ 7. Export File List
│   │   └─ Save file list with metadata to text file
│   │
│   └─ 0. Back to Main Menu
│
├─ 5. SETTINGS & TOOLS
│   │
│   ├─ 1. View Configuration
│   │   └─ Display all current settings
│   │
│   ├─ 2. Edit Configuration
│   │   ├─ Open config.yaml in text editor
│   │   └─ Restart required for changes
│   │
│   ├─ 3. Check Memory Status
│   │   ├─ Display RAM usage (total/available/free)
│   │   ├─ Display swap usage
│   │   ├─ Recommendations based on available memory
│   │   └─ Swap setup instructions if needed
│   │
│   ├─ 4. Test Microphone
│   │   ├─ Display default microphone info
│   │   ├─ Test recording for 3 seconds
│   │   └─ Confirm microphone works
│   │
│   ├─ 5. Ollama Model Management
│   │   ├─ List installed models
│   │   ├─ Pull/download new model
│   │   ├─ Remove model
│   │   └─ Check Ollama service status
│   │
│   ├─ 6. Cache Management
│   │   ├─ View cache statistics
│   │   │   ├─ Hit rate percentage
│   │   │   ├─ Memory usage
│   │   │   ├─ Cached items count
│   │   │   └─ Cache effectiveness
│   │   ├─ Clear file cache
│   │   ├─ Clear correction cache
│   │   └─ Clear all caches
│   │
│   ├─ 7. View Logs
│   │   ├─ View recent logs (last 50 lines)
│   │   ├─ View all logs
│   │   ├─ Search logs by term
│   │   └─ Clear logs
│   │
│   ├─ 8. System Diagnostics
│   │   ├─ Python version
│   │   ├─ Installed packages (vosk, pyaudio, ollama)
│   │   ├─ Vosk model status and size
│   │   ├─ Output folder status
│   │   ├─ Available memory
│   │   └─ Cache performance
│   │
│   └─ 0. Back to Main Menu
│
├─ 6. VIEW OPTIONS TREE (this menu!)
│   └─ Display complete application structure
│
├─ 7. CHECK MEMORY STATUS
│   └─ Quick memory check without entering settings
│
└─ 0. EXIT
    └─ Gracefully shut down application

════════════════════════════════════════════════════════════════

KEYBOARD SHORTCUTS:
  Ctrl+C    Stop recording / Interrupt operation
  Ctrl+D    EOF / Exit input prompt
  0         Back / Cancel in any menu

RESOURCE USAGE BY MODE:
  Mode 1 (Transcribe):  ~6-8GB RAM (Vosk only)
  Mode 2 (Correct):     ~4-5GB RAM (Ollama only)
  Mode 3 (Full):        ~6-8GB RAM peak (sequential loading)
  Mode 4 (Files):       ~100-200MB RAM (no models)
  Mode 5 (Settings):    ~100-200MB RAM (no models)

TIPS:
  • Use Mode 1 or 2 separately to save memory
  • Mode 3 loads models sequentially (never both at once)
  • Mode 4 for file management without loading models
  • Check cache stats regularly for performance insights
  • Add swap space if you have < 8GB free RAM

════════════════════════════════════════════════════════════════
"""
    
    print(tree)
    
    # Wait for user
    input("\nPress Enter to return to main menu...")


def show_quick_help():
    """Show quick help summary."""
    help_text = """
╔══════════════════════════════════════════════════════════════╗
║                      QUICK REFERENCE                          ║
╚══════════════════════════════════════════════════════════════╝

MODES:
  1 - Record only (transcription)
  2 - Fix files only (AI correction)
  3 - Record then fix (complete workflow)
  4 - Manage files (view, search, delete, merge)
  5 - Settings and tools

COMMON TASKS:
  Record a meeting     → Mode 1 → Option 1
  Fix old file         → Mode 2 → Option 2
  Quick transcription  → Mode 3 (all-in-one)
  Find something       → Mode 4 → Option 3 (search)
  Check performance    → Mode 5 → Option 6 (cache stats)

MEMORY TIPS:
  • Close browsers before loading large models
  • Use Mode 1 or 2 separately if low on RAM
  • Add swap: sudo fallocate -l 8G /swapfile
  • Check status: Mode 7 or Mode 5 → Option 3

For complete options tree, select Option 6 from main menu.
═══════════════════════════════════════════════════════════════
"""
    print(help_text)
