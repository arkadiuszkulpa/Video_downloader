"""Complete Tkinter GUI for Video Downloader Pipeline.

Includes all three operations: Download, Transcribe, Analyze + Full Pipeline.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import os

from core import Downloader, Transcriber, Analyzer, Pipeline, AuthManager
from utils import ProgressCallback, validate_url, validate_directory, validate_file_exists
from gui.widgets import LogOutput, ProgressPanel, FileSelector


class VideoDownloaderApp(tk.Tk):
    """Complete video downloader application with tabbed interface."""

    def __init__(self):
        super().__init__()

        self.title("Video Downloader & Transcription Pipeline")
        self.geometry("900x700")

        # State
        self.worker_thread = None
        self.progress_queue = None

        # Create UI
        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main notebook (tabbed interface)
        self.notebook = ttk.Notebook(self, padding="10")
        self.notebook.pack(fill='both', expand=True)

        # Create tabs
        self.download_tab = self._create_download_tab()
        self.transcribe_tab = self._create_transcribe_tab()
        self.analyze_tab = self._create_analyze_tab()
        self.pipeline_tab = self._create_pipeline_tab()

        self.notebook.add(self.download_tab, text="Download")
        self.notebook.add(self.transcribe_tab, text="Transcribe")
        self.notebook.add(self.analyze_tab, text="Analyze")
        self.notebook.add(self.pipeline_tab, text="Full Pipeline")

    def _create_download_tab(self):
        """Create download-only tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(3, weight=1)

        # URL
        ttk.Label(tab, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.dl_url_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.dl_url_var, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Output directory
        ttk.Label(tab, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dl_output_selector = FileSelector(tab, mode='directory')
        self.dl_output_selector.set_path("dump")
        self.dl_output_selector.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Options
        self.dl_no_auth_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Skip authentication (public URLs)", variable=self.dl_no_auth_var).grid(row=2, column=1, sticky=tk.W, pady=5)

        # Progress and log
        self.dl_progress = ProgressPanel(tab)
        self.dl_progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.dl_log = LogOutput(tab)
        self.dl_log.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        self.dl_start_btn = ttk.Button(btn_frame, text="Start Download", command=self._start_download)
        self.dl_start_btn.grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Clear Log", command=self.dl_log.clear).grid(row=0, column=1, padx=5)

        return tab

    def _create_transcribe_tab(self):
        """Create transcription-only tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(4, weight=1)

        # Input file
        ttk.Label(tab, text="Audio/Video File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.tr_input_selector = FileSelector(tab, mode='file')
        self.tr_input_selector.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Output directory
        ttk.Label(tab, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.tr_output_selector = FileSelector(tab, mode='directory')
        self.tr_output_selector.set_path("dump")
        self.tr_output_selector.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Options
        opt_frame = ttk.Frame(tab)
        opt_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(opt_frame, text="Device:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.tr_device_var = tk.StringVar(value="cpu")
        device_combo = ttk.Combobox(opt_frame, textvariable=self.tr_device_var, values=["cpu", "cuda"], state='readonly', width=10)
        device_combo.grid(row=0, column=1, padx=5)

        ttk.Label(opt_frame, text="Model:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.tr_model_var = tk.StringVar(value="base")
        model_combo = ttk.Combobox(opt_frame, textvariable=self.tr_model_var,
                                   values=["tiny", "base", "small", "medium", "large"], state='readonly', width=10)
        model_combo.grid(row=0, column=3, padx=5)

        # Progress and log
        self.tr_progress = ProgressPanel(tab)
        self.tr_progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.tr_log = LogOutput(tab)
        self.tr_log.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        self.tr_start_btn = ttk.Button(btn_frame, text="Start Transcription", command=self._start_transcribe)
        self.tr_start_btn.grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Clear Log", command=self.tr_log.clear).grid(row=0, column=1, padx=5)

        return tab

    def _create_analyze_tab(self):
        """Create analysis-only tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(5, weight=1)

        # Input transcript
        ttk.Label(tab, text="Transcript File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.an_input_selector = FileSelector(tab, mode='file')
        self.an_input_selector.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Output directory
        ttk.Label(tab, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.an_output_selector = FileSelector(tab, mode='directory')
        self.an_output_selector.set_path("dump")
        self.an_output_selector.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Authentication
        auth_frame = ttk.LabelFrame(tab, text="Authentication", padding="10")
        auth_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        auth_frame.columnconfigure(1, weight=1)

        self.an_auth_method_var = tk.StringVar(value="direct")
        ttk.Radiobutton(auth_frame, text="AWS Secrets Manager", variable=self.an_auth_method_var,
                       value="aws", command=self._toggle_auth_fields).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(auth_frame, text="Direct API Key", variable=self.an_auth_method_var,
                       value="direct", command=self._toggle_auth_fields).grid(row=0, column=1, sticky=tk.W)

        # AWS fields
        self.an_aws_frame = ttk.Frame(auth_frame)
        ttk.Label(self.an_aws_frame, text="Secret Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.an_secret_name_var = tk.StringVar(value="anthropic/other")
        ttk.Entry(self.an_aws_frame, textvariable=self.an_secret_name_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        ttk.Label(self.an_aws_frame, text="Region:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.an_region_var = tk.StringVar(value="eu-west-2")
        ttk.Entry(self.an_aws_frame, textvariable=self.an_region_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)

        # Direct API key field
        self.an_direct_frame = ttk.Frame(auth_frame)
        ttk.Label(self.an_direct_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.an_api_key_var = tk.StringVar()
        ttk.Entry(self.an_direct_frame, textvariable=self.an_api_key_var, show='*', width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)

        self._toggle_auth_fields()

        # Progress and log
        self.an_progress = ProgressPanel(tab)
        self.an_progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.an_log = LogOutput(tab)
        self.an_log.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        self.an_start_btn = ttk.Button(btn_frame, text="Start Analysis", command=self._start_analyze)
        self.an_start_btn.grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Clear Log", command=self.an_log.clear).grid(row=0, column=1, padx=5)

        return tab

    def _create_pipeline_tab(self):
        """Create full pipeline tab."""
        tab = ttk.Frame(self.notebook, padding="10")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(4, weight=1)

        # URL
        ttk.Label(tab, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pl_url_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.pl_url_var, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Output directory
        ttk.Label(tab, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pl_output_selector = FileSelector(tab, mode='directory')
        self.pl_output_selector.set_path("dump")
        self.pl_output_selector.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # Authentication (same as analyze tab)
        auth_frame = ttk.LabelFrame(tab, text="API Authentication", padding="10")
        auth_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        auth_frame.columnconfigure(1, weight=1)

        self.pl_auth_method_var = tk.StringVar(value="direct")
        ttk.Radiobutton(auth_frame, text="AWS", variable=self.pl_auth_method_var,
                       value="aws", command=self._toggle_pl_auth_fields).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(auth_frame, text="Direct", variable=self.pl_auth_method_var,
                       value="direct", command=self._toggle_pl_auth_fields).grid(row=0, column=1, sticky=tk.W)

        self.pl_aws_frame = ttk.Frame(auth_frame)
        ttk.Label(self.pl_aws_frame, text="Secret:").grid(row=0, column=0)
        self.pl_secret_name_var = tk.StringVar(value="anthropic/other")
        ttk.Entry(self.pl_aws_frame, textvariable=self.pl_secret_name_var, width=20).grid(row=0, column=1, padx=5)
        ttk.Label(self.pl_aws_frame, text="Region:").grid(row=0, column=2)
        self.pl_region_var = tk.StringVar(value="eu-west-2")
        ttk.Entry(self.pl_aws_frame, textvariable=self.pl_region_var, width=15).grid(row=0, column=3, padx=5)

        self.pl_direct_frame = ttk.Frame(auth_frame)
        ttk.Label(self.pl_direct_frame, text="API Key:").grid(row=0, column=0)
        self.pl_api_key_var = tk.StringVar()
        ttk.Entry(self.pl_direct_frame, textvariable=self.pl_api_key_var, show='*', width=50).grid(row=0, column=1, padx=5)

        self._toggle_pl_auth_fields()

        # Options
        opt_frame = ttk.LabelFrame(tab, text="Options", padding="10")
        opt_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(opt_frame, text="Transcription Device:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.pl_device_var = tk.StringVar(value="cpu")
        ttk.Combobox(opt_frame, textvariable=self.pl_device_var, values=["cpu", "cuda"], state='readonly', width=10).grid(row=0, column=1, padx=5)

        ttk.Label(opt_frame, text="Model:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.pl_model_var = tk.StringVar(value="base")
        ttk.Combobox(opt_frame, textvariable=self.pl_model_var,
                    values=["tiny", "base", "small", "medium"], state='readonly', width=10).grid(row=0, column=3, padx=5)

        self.pl_no_auth_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Skip download authentication", variable=self.pl_no_auth_var).grid(row=0, column=4, sticky=tk.W, padx=10)

        # Progress and log
        self.pl_progress = ProgressPanel(tab)
        self.pl_progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.pl_log = LogOutput(tab)
        self.pl_log.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        self.pl_start_btn = ttk.Button(btn_frame, text="Start Full Pipeline", command=self._start_pipeline)
        self.pl_start_btn.grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Clear Log", command=self.pl_log.clear).grid(row=0, column=1, padx=5)

        return tab

    def _toggle_auth_fields(self):
        """Toggle AWS/Direct auth fields for analyze tab."""
        self.an_aws_frame.grid_forget()
        self.an_direct_frame.grid_forget()

        if self.an_auth_method_var.get() == "aws":
            self.an_aws_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        else:
            self.an_direct_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    def _toggle_pl_auth_fields(self):
        """Toggle AWS/Direct auth fields for pipeline tab."""
        self.pl_aws_frame.grid_forget()
        self.pl_direct_frame.grid_forget()

        if self.pl_auth_method_var.get() == "aws":
            self.pl_aws_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        else:
            self.pl_direct_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

    # Operation handlers
    def _start_download(self):
        """Start download operation."""
        url = self.dl_url_var.get().strip()
        output_dir = self.dl_output_selector.get_path()

        is_valid, error = validate_url(url)
        if not is_valid:
            messagebox.showerror("Invalid URL", error)
            return

        is_valid, error = validate_directory(output_dir)
        if not is_valid:
            messagebox.showerror("Invalid Directory", error)
            return

        self.dl_start_btn.config(state='disabled')
        self.dl_progress.reset()
        self.dl_log.append("Starting download...", "info")

        self.progress_queue = queue.Queue()
        self.worker_thread = threading.Thread(
            target=self._download_worker,
            args=(url, output_dir, self.dl_no_auth_var.get()),
            daemon=True
        )
        self.worker_thread.start()
        self.after(100, lambda: self._check_queue(self.dl_progress, self.dl_log, self.dl_start_btn))

    def _download_worker(self, url, output_dir, no_auth):
        """Download worker thread."""
        try:
            callback = ProgressCallback(self.progress_queue)
            downloader = Downloader(progress_callback=callback)
            success, output_file, message = downloader.download(url, output_dir, no_auth=no_auth)
            callback.complete(success, message)
        except Exception as e:
            self.progress_queue.put({'type': 'error', 'message': str(e)})

    def _start_transcribe(self):
        """Start transcription operation."""
        input_file = self.tr_input_selector.get_path()
        output_dir = self.tr_output_selector.get_path()

        is_valid, error = validate_file_exists(input_file)
        if not is_valid:
            messagebox.showerror("Invalid File", error)
            return

        is_valid, error = validate_directory(output_dir)
        if not is_valid:
            messagebox.showerror("Invalid Directory", error)
            return

        self.tr_start_btn.config(state='disabled')
        self.tr_progress.reset()
        self.tr_log.append("Starting transcription...", "info")

        self.progress_queue = queue.Queue()
        self.worker_thread = threading.Thread(
            target=self._transcribe_worker,
            args=(input_file, output_dir, self.tr_device_var.get(), self.tr_model_var.get()),
            daemon=True
        )
        self.worker_thread.start()
        self.after(100, lambda: self._check_queue(self.tr_progress, self.tr_log, self.tr_start_btn))

    def _transcribe_worker(self, input_file, output_dir, device, model_size):
        """Transcription worker thread."""
        try:
            callback = ProgressCallback(self.progress_queue)
            transcriber = Transcriber(progress_callback=callback)
            success, output_file, message = transcriber.transcribe(input_file, output_dir, device, model_size)
            callback.complete(success, message)
        except Exception as e:
            self.progress_queue.put({'type': 'error', 'message': str(e)})

    def _start_analyze(self):
        """Start analysis operation."""
        input_file = self.an_input_selector.get_path()
        output_dir = self.an_output_selector.get_path()

        is_valid, error = validate_file_exists(input_file)
        if not is_valid:
            messagebox.showerror("Invalid File", error)
            return

        is_valid, error = validate_directory(output_dir)
        if not is_valid:
            messagebox.showerror("Invalid Directory", error)
            return

        # Build auth config
        auth_config = self._get_auth_config(
            self.an_auth_method_var.get(),
            self.an_secret_name_var.get(),
            self.an_region_var.get(),
            self.an_api_key_var.get()
        )

        self.an_start_btn.config(state='disabled')
        self.an_progress.reset()
        self.an_log.append("Starting analysis...", "info")

        self.progress_queue = queue.Queue()
        self.worker_thread = threading.Thread(
            target=self._analyze_worker,
            args=(input_file, output_dir, auth_config),
            daemon=True
        )
        self.worker_thread.start()
        self.after(100, lambda: self._check_queue(self.an_progress, self.an_log, self.an_start_btn))

    def _analyze_worker(self, input_file, output_dir, auth_config):
        """Analysis worker thread."""
        try:
            callback = ProgressCallback(self.progress_queue)
            api_key = AuthManager.get_api_key(**auth_config)
            analyzer = Analyzer(progress_callback=callback)
            success, output_file, message = analyzer.analyze(input_file, output_dir, api_key)
            callback.complete(success, message)
        except Exception as e:
            self.progress_queue.put({'type': 'error', 'message': str(e)})

    def _start_pipeline(self):
        """Start full pipeline operation."""
        url = self.pl_url_var.get().strip()
        output_dir = self.pl_output_selector.get_path()

        is_valid, error = validate_url(url)
        if not is_valid:
            messagebox.showerror("Invalid URL", error)
            return

        is_valid, error = validate_directory(output_dir)
        if not is_valid:
            messagebox.showerror("Invalid Directory", error)
            return

        auth_config = self._get_auth_config(
            self.pl_auth_method_var.get(),
            self.pl_secret_name_var.get(),
            self.pl_region_var.get(),
            self.pl_api_key_var.get()
        )

        self.pl_start_btn.config(state='disabled')
        self.pl_progress.reset()
        self.pl_log.append("Starting full pipeline...", "info")

        self.progress_queue = queue.Queue()
        self.worker_thread = threading.Thread(
            target=self._pipeline_worker,
            args=(url, output_dir, auth_config, self.pl_device_var.get(),
                  self.pl_model_var.get(), self.pl_no_auth_var.get()),
            daemon=True
        )
        self.worker_thread.start()
        self.after(100, lambda: self._check_queue(self.pl_progress, self.pl_log, self.pl_start_btn))

    def _pipeline_worker(self, url, output_dir, auth_config, device, model_size, no_auth):
        """Pipeline worker thread."""
        try:
            callback = ProgressCallback(self.progress_queue)
            pipeline = Pipeline(progress_callback=callback)
            success, results, message = pipeline.run(
                url, output_dir, auth_config, device=device, model_size=model_size, no_auth=no_auth
            )
            callback.complete(success, message)
        except Exception as e:
            self.progress_queue.put({'type': 'error', 'message': str(e)})

    def _get_auth_config(self, method, secret_name, region, api_key):
        """Build auth config dictionary."""
        if method == 'aws':
            return {'method': 'aws', 'secret_name': secret_name, 'region_name': region}
        else:
            return {'method': 'direct', 'api_key': api_key}

    def _check_queue(self, progress_panel, log_widget, start_button):
        """Poll progress queue for updates."""
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                msg_type = msg.get('type')

                if msg_type == 'progress':
                    percent = msg.get('percent', 0)
                    message = msg.get('message', '')
                    progress_panel.update_progress(percent, message)

                elif msg_type == 'log':
                    message = msg.get('message', '')
                    level = msg.get('level', 'info')
                    log_widget.append(message, level)

                elif msg_type == 'complete':
                    success = msg.get('success', False)
                    message = msg.get('message', '')
                    progress_panel.set_progress(100 if success else 0)
                    progress_panel.set_status("Complete" if success else "Failed")
                    start_button.config(state='normal')
                    if success:
                        log_widget.append(message, 'success')
                        messagebox.showinfo("Success", message)
                    else:
                        log_widget.append(message, 'error')
                        messagebox.showerror("Error", message)

                elif msg_type == 'error':
                    message = msg.get('message', 'Unknown error')
                    log_widget.append(message, 'error')
                    progress_panel.set_status("Error")
                    start_button.config(state='normal')
                    messagebox.showerror("Error", message)

        except queue.Empty:
            pass

        if self.worker_thread and self.worker_thread.is_alive():
            self.after(100, lambda: self._check_queue(progress_panel, log_widget, start_button))


def main():
    """Entry point for complete GUI."""
    app = VideoDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
