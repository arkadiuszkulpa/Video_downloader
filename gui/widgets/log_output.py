"""Scrolled text log widget with color coding."""

import tkinter as tk
from tkinter import scrolledtext


class LogOutput(scrolledtext.ScrolledText):
    """
    Scrolled text widget for log output with color-coded log levels.

    Features:
    - Auto-scroll to bottom on new messages
    - Color coding by log level (info, warning, error, debug)
    - Programmatic clear functionality
    - Read-only mode
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize log output widget.

        Args:
            parent: Parent widget
            **kwargs: Additional arguments passed to ScrolledText
        """
        # Set default kwargs
        kwargs.setdefault('wrap', tk.WORD)
        kwargs.setdefault('height', 15)
        kwargs.setdefault('width', 80)

        super().__init__(parent, **kwargs)

        # Configure as read-only
        self.config(state='disabled')

        # Configure color tags
        self.tag_config('info', foreground='black')
        self.tag_config('warning', foreground='orange')
        self.tag_config('error', foreground='red')
        self.tag_config('debug', foreground='gray')
        self.tag_config('success', foreground='green')

    def append(self, message, level='info'):
        """
        Append message to log with specified level.

        Args:
            message (str): Message to append
            level (str): Log level (info, warning, error, debug, success)
        """
        # Enable editing temporarily
        self.config(state='normal')

        # Append message with color tag
        self.insert(tk.END, f"[{level.upper()}] {message}\n", level)

        # Auto-scroll to bottom
        self.see(tk.END)

        # Disable editing
        self.config(state='disabled')

    def clear(self):
        """Clear all log output."""
        self.config(state='normal')
        self.delete('1.0', tk.END)
        self.config(state='disabled')

    def get_text(self):
        """
        Get all log text.

        Returns:
            str: All log content
        """
        return self.get('1.0', tk.END)
