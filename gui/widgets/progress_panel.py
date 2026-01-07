"""Combined progress bar and status label widget."""

import tkinter as tk
from tkinter import ttk


class ProgressPanel(ttk.Frame):
    """
    Combined progress bar with status label.

    Features:
    - Progress bar with percentage display
    - Status label showing current operation
    - Determinate and indeterminate modes
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize progress panel.

        Args:
            parent: Parent widget
            **kwargs: Additional arguments passed to Frame
        """
        super().__init__(parent, **kwargs)

        # Configure grid
        self.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, sticky=tk.W)

    def set_progress(self, percent):
        """
        Set progress bar percentage.

        Args:
            percent (float): Progress percentage (0-100)
        """
        self.progress_var.set(percent)

    def set_status(self, status):
        """
        Set status label text.

        Args:
            status (str): Status message
        """
        self.status_var.set(status)

    def update_progress(self, percent, status):
        """
        Update both progress and status.

        Args:
            percent (float): Progress percentage (0-100)
            status (str): Status message
        """
        self.set_progress(percent)
        self.set_status(status)

    def reset(self):
        """Reset progress to 0 and status to 'Ready'."""
        self.progress_var.set(0)
        self.status_var.set("Ready")

    def set_indeterminate(self):
        """Switch to indeterminate mode (for unknown progress)."""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)  # Animation speed

    def set_determinate(self):
        """Switch to determinate mode (for known progress)."""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
