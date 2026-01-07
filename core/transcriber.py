"""Audio transcription with progress callback support."""

import os
import torch
from faster_whisper import WhisperModel


class Transcriber:
    """
    Audio transcription using Whisper AI with progress callbacks.

    Supports:
    - CPU and CUDA (GPU) inference
    - Multiple model sizes (tiny, base, small, medium, large)
    - Progress reporting per segment
    - Automatic output filename generation
    """

    AVAILABLE_MODELS = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
    AVAILABLE_DEVICES = ['cpu', 'cuda']

    def __init__(self, progress_callback=None):
        """
        Initialize transcriber.

        Args:
            progress_callback (ProgressCallback, optional): Callback for progress updates
        """
        self.progress_callback = progress_callback
        self._model = None
        self._current_model_size = None
        self._current_device = None

    def transcribe(self, audio_file, output_dir, device='cpu', model_size='base'):
        """
        Transcribe audio file to text.

        Args:
            audio_file (str): Path to audio or video file
            output_dir (str): Output directory for transcript
            device (str): 'cpu' or 'cuda' for GPU acceleration
            model_size (str): Whisper model size ('tiny', 'base', 'small', 'medium', 'large')

        Returns:
            tuple: (success: bool, transcript_file: str, message: str)
        """
        try:
            # Validate inputs
            if not os.path.exists(audio_file):
                return False, "", f"Audio file not found: {audio_file}"

            if not os.path.isfile(audio_file):
                return False, "", f"Path is not a file: {audio_file}"

            # Validate device
            if device not in self.AVAILABLE_DEVICES:
                return False, "", f"Invalid device: {device}. Must be 'cpu' or 'cuda'"

            # Check CUDA availability
            if device == 'cuda' and not torch.cuda.is_available():
                self._log("CUDA not available, falling back to CPU", "warning")
                device = 'cpu'

            # Validate model size
            if model_size not in self.AVAILABLE_MODELS:
                return False, "", f"Invalid model size: {model_size}. Choose from: {', '.join(self.AVAILABLE_MODELS)}"

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate output filename
            audio_basename = os.path.splitext(os.path.basename(audio_file))[0]
            transcript_file = os.path.join(output_dir, f"{audio_basename}_transcript.txt")

            # Log device info
            self._log_device_info(device)

            # Load model (reuse if same model/device)
            self._log(f"Loading Whisper model: {model_size} ({device})", "info")
            model = self._get_model(model_size, device)

            # Transcribe
            self._log(f"Transcribing: {audio_file}", "info")
            self._log("This may take a while for large files...", "info")

            # Signal indeterminate progress (we don't know duration in advance)
            if self.progress_callback:
                self.progress_callback.update('transcribe', 0, 100, "Transcribing audio...")

            segments, info = model.transcribe(audio_file)

            # Write transcript with progress tracking
            self._log("Writing transcript...", "info")
            segment_count = 0

            with open(transcript_file, "w", encoding="utf-8") as f:
                for segment in segments:
                    f.write(segment.text + "\n")
                    segment_count += 1

                    # Update progress every 5 segments
                    if segment_count % 5 == 0:
                        message = f"Processed {segment_count} segments..."
                        if self.progress_callback:
                            # Use segment count as a progress indicator (max 100 for display)
                            # This gives visual feedback even though we don't know total
                            display_progress = min(segment_count * 2, 95)  # Cap at 95% until done
                            self.progress_callback.update('transcribe', display_progress, 100, message)
                        self._log(message, "info")

            # Final progress update
            if self.progress_callback:
                self.progress_callback.update('transcribe', 100, 100,
                    f"Transcription complete: {segment_count} segments")

            self._log(f"Transcription complete: {segment_count} segments", "info")
            self._log(f"Saved to: {transcript_file}", "info")

            return True, transcript_file, f"Transcription complete ({segment_count} segments)"

        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            self._log(error_msg, "error")
            if self.progress_callback:
                self.progress_callback.error(error_msg, e)
            return False, "", error_msg

    def _get_model(self, model_size, device):
        """
        Load Whisper model, reusing if already loaded.

        Args:
            model_size (str): Model size
            device (str): Device to use

        Returns:
            WhisperModel: Loaded model
        """
        # Reuse model if already loaded with same parameters
        if (self._model is not None and
            self._current_model_size == model_size and
            self._current_device == device):
            self._log("Reusing loaded model", "info")
            return self._model

        # Load new model
        self._log(f"Loading model '{model_size}' on {device}...", "info")

        # First-time download notice
        if not self._is_model_cached(model_size):
            self._log(f"Model '{model_size}' will be downloaded on first use (~{self._get_model_size_estimate(model_size)})", "info")
            self._log("This is a one-time download and may take a few minutes...", "info")

        self._model = WhisperModel(model_size, device=device)
        self._current_model_size = model_size
        self._current_device = device

        return self._model

    def _is_model_cached(self, model_size):
        """
        Check if model is already cached locally.

        Args:
            model_size (str): Model size to check

        Returns:
            bool: True if model is cached
        """
        # Whisper models are cached in user's home directory
        # This is a simplified check - actual cache location varies by OS
        try:
            import huggingface_hub
            cache_dir = huggingface_hub.constants.HF_HUB_CACHE
            # Look for model files
            model_path = os.path.join(cache_dir, f"models--Systran--faster-whisper-{model_size}")
            return os.path.exists(model_path)
        except:
            # If we can't determine, assume not cached
            return False

    def _get_model_size_estimate(self, model_size):
        """
        Get estimated download size for model.

        Args:
            model_size (str): Model size

        Returns:
            str: Human-readable size estimate
        """
        sizes = {
            'tiny': '75 MB',
            'base': '145 MB',
            'small': '470 MB',
            'medium': '1.5 GB',
            'large': '3 GB',
            'large-v2': '3 GB',
            'large-v3': '3 GB',
        }
        return sizes.get(model_size, 'unknown size')

    def _log_device_info(self, device):
        """Log information about compute device."""
        if device == 'cuda':
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                self._log(f"Using CUDA GPU: {device_name}", "info")
            else:
                self._log("CUDA not available, using CPU", "warning")
        else:
            self._log("Using CPU for transcription", "info")

    @staticmethod
    def check_cuda_available():
        """
        Check if CUDA (GPU acceleration) is available.

        Returns:
            tuple: (available: bool, device_name: str or None)
        """
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            return True, device_name
        return False, None

    def _log(self, message, level='info'):
        """Send log message via callback or print."""
        if self.progress_callback:
            self.progress_callback.log(message, level)
        else:
            print(f"[{level.upper()}] {message}")
