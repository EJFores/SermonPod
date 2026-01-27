#!/usr/bin/env python3
"""
SermonPod - YouTube to MP3 Converter
Main entry point for the application.
"""

import sys

from .gui.main_window import SermonPodGUI, create_main_window


def main():
    """Main application entry point."""
    try:
        # Create main window
        root = create_main_window()

        # Create application
        SermonPodGUI(root)

        # Start main loop
        root.mainloop()

    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
