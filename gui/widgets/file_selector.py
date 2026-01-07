"""File and directory selector widget."""

import tkinter as tk
from tkinter import ttk, filedialog
import os


class FileSelector(ttk.Frame):
    """
    File or directory selector with entry field and browse button.

    Features:
    - Entry field for manual path input
    - Browse button for dialog selection
    - Validation indicator (optional)
    - Support for files and directories
    """

    def __init__(self, parent, mode='file', **kwargs):
        """
        Initialize file selector.

        Args:
            parent: Parent widget
            mode (str): Selection mode - 'file', 'directory', or 'save'
            **kwargs: Additional arguments passed to Frame
        """
        super().__init__(parent, **kwargs)

        self.mode = mode

        # Configure grid
        self.columnconfigure(0, weight=1)

        # Path variable
        self.path_var = tk.StringVar()
        self.path_var.trace('w', self._on_path_change)

        # Entry field
        self.entry = ttk.Entry(self, textvariable=self.path_var)
        self.entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        # Browse button
        self.browse_button = ttk.Button(self, text="Browse...", command=self._browse)
        self.browse_button.grid(row=0, column=1)

    def _browse(self):
        """Open file/directory dialog."""
        if self.mode == 'file':
            path = filedialog.askopenfilename(
                title="Select File",
                initialdir=os.path.dirname(self.path_var.get()) or os.getcwd()
            )
        elif self.mode == 'directory':
            path = filedialog.askdirectory(
                title="Select Directory",
                initialdir=self.path_var.get() or os.getcwd()
            )
        elif self.mode == 'save':
            path = filedialog.asksaveasfilename(
                title="Save As",
                initialdir=os.path.dirname(self.path_var.get()) or os.getcwd()
            )
        else:
            raise ValueError(f"Invalid mode: {self.mode}")

        if path:
            self.path_var.set(path)

    def _on_path_change(self, *args):
        """Called when path changes (for validation, etc.)."""
        # Subclasses can override for validation
        pass

    def get_path(self):
        """
        Get current path.

        Returns:
            str: Selected path
        """
        return self.path_var.get().strip()

    def set_path(self, path):
        """
        Set path value.

        Args:
            path (str): Path to set
        """
        self.path_var.set(path)

    def clear(self):
        """Clear path value."""
        self.path_var.set("")

    def disable(self):
        """Disable widget."""
        self.entry.config(state='disabled')
        self.browse_button.config(state='disabled')

    def enable(self):
        """Enable widget."""
        self.entry.config(state='normal')
        self.browse_button.config(state='normal')


class ValidatedFileSelector(FileSelector):
    """
    File selector with visual validation feedback.

    Shows green checkmark if path exists, red X if not.
    """

    def __init__(self, parent, mode='file', **kwargs):
        super().__init__(parent, mode, **kwargs)

        # Validation label
        self.validation_label = ttk.Label(self, text="")
        self.validation_label.grid(row=0, column=2, padx=(5, 0))

    def _on_path_change(self, *args):
        """Validate path and update indicator."""
        path = self.get_path()

        if not path:
            self.validation_label.config(text="", foreground="black")
            return

        if self.mode == 'directory':
            exists = os.path.isdir(path)
        else:  # file or save
            exists = os.path.exists(path)

        if exists:
            self.validation_label.config(text="✓", foreground="green")
        else:
            self.validation_label.config(text="✗", foreground="red")
