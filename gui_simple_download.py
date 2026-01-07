"""Simple GUI for video/audio downloader - Proof of Concept."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os

from core.downloader import Downloader
from utils.progress_callback import ProgressCallback
from utils.validators import validate_url, validate_directory


class SimpleDownloaderGUI(tk.Tk):
    """Simple downloader GUI - proof of concept."""

    def __init__(self):
        super().__init__()

        self.title("Video/Audio Downloader")
        self.geometry("800x600")

        # State
        self.worker_thread = None
        self.progress_queue = None

        # Create UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # URL Input
        ttk.Label(main_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Output Directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)

        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        dir_frame.columnconfigure(0, weight=1)

        self.output_dir_var = tk.StringVar(value="dump")
        ttk.Entry(dir_frame, textvariable=self.output_dir_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dir_frame, text="Browse...", command=self._browse_directory).grid(row=0, column=1)

        # No Auth Checkbox
        self.no_auth_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Skip authentication (for public URLs)",
                        variable=self.no_auth_var).grid(row=2, column=1, sticky=tk.W, pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start Download", command=self._start_download)
        self.start_button.grid(row=0, column=0, padx=5)

        ttk.Button(button_frame, text="Clear Log", command=self._clear_log).grid(row=0, column=1, padx=5)

        # Progress Bar
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=2)

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)

        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure text tags for colored output
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('debug', foreground='gray')

    def _browse_directory(self):
        """Open directory browser dialog."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get() or os.getcwd()
        )
        if directory:
            self.output_dir_var.set(directory)

    def _clear_log(self):
        """Clear log output."""
        self.log_text.delete('1.0', tk.END)

    def _log_message(self, message, level='info'):
        """
        Add message to log widget.

        Args:
            message (str): Message to log
            level (str): Log level (info, warning, error, debug)
        """
        self.log_text.insert(tk.END, f"[{level.upper()}] {message}\n", level)
        self.log_text.see(tk.END)  # Auto-scroll

    def _start_download(self):
        """Start download in background thread."""
        # Validate inputs
        url = self.url_var.get().strip()
        output_dir = self.output_dir_var.get().strip()

        # Validate URL
        is_valid, error = validate_url(url)
        if not is_valid:
            messagebox.showerror("Invalid URL", error)
            return

        # Validate directory
        is_valid, error = validate_directory(output_dir)
        if not is_valid:
            messagebox.showerror("Invalid Directory", error)
            return

        # Disable start button
        self.start_button.config(state='disabled')

        # Reset progress
        self.progress_var.set(0)
        self.status_label.config(text="Starting download...")
        self._log_message("Download started", "info")

        # Create progress queue
        self.progress_queue = queue.Queue()

        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self._download_worker,
            args=(url, output_dir, self.no_auth_var.get()),
            daemon=True
        )
        self.worker_thread.start()

        # Start queue polling
        self.after(100, self._check_queue)

    def _download_worker(self, url, output_dir, no_auth):
        """
        Worker thread for download operation.

        Args:
            url (str): Download URL
            output_dir (str): Output directory
            no_auth (bool): Skip authentication
        """
        try:
            callback = ProgressCallback(self.progress_queue)
            downloader = Downloader(progress_callback=callback)

            callback.log("Initializing download...", "info")

            success, output_file, message = downloader.download(
                url=url,
                output_dir=output_dir,
                no_auth=no_auth
            )

            callback.complete(success, message if success else f"Download failed: {message}")

            if success:
                callback.log(f"File saved to: {output_file}", "info")

        except Exception as e:
            self.progress_queue.put({
                'type': 'error',
                'message': f"Unexpected error: {str(e)}"
            })

    def _check_queue(self):
        """Poll progress queue for updates from worker thread."""
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                self._process_queue_message(msg)
        except queue.Empty:
            pass

        # Continue polling if thread is alive
        if self.worker_thread and self.worker_thread.is_alive():
            self.after(100, self._check_queue)

    def _process_queue_message(self, msg):
        """
        Process message from worker thread.

        Args:
            msg (dict): Message dictionary with 'type' and other fields
        """
        msg_type = msg.get('type')

        if msg_type == 'progress':
            # Update progress bar
            percent = msg.get('percent', 0)
            self.progress_var.set(percent)

            # Update status label
            message = msg.get('message', '')
            self.status_label.config(text=message)

            # Log progress
            if message:
                self._log_message(message, 'debug')

        elif msg_type == 'log':
            # Log message
            message = msg.get('message', '')
            level = msg.get('level', 'info')
            self._log_message(message, level)

        elif msg_type == 'complete':
            # Operation complete
            success = msg.get('success', False)
            message = msg.get('message', '')

            self.progress_var.set(100 if success else 0)
            self.status_label.config(text="Complete" if success else "Failed")
            self.start_button.config(state='normal')

            if success:
                self._log_message(message, 'info')
                messagebox.showinfo("Success", message)
            else:
                self._log_message(message, 'error')
                messagebox.showerror("Error", message)

        elif msg_type == 'error':
            # Error occurred
            message = msg.get('message', 'Unknown error')
            self._log_message(message, 'error')
            self.status_label.config(text="Error")
            self.start_button.config(state='normal')
            messagebox.showerror("Error", message)


def main():
    """Entry point for simple downloader GUI."""
    app = SimpleDownloaderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
