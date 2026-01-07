"""Full pipeline orchestrator: Download → Transcribe → Analyze."""

from .downloader import Downloader
from .transcriber import Transcriber
from .analyzer import Analyzer
from .auth_manager import AuthManager


class Pipeline:
    """
    Orchestrates the full video processing pipeline.

    Pipeline stages:
    1. Download: Fetch video/audio from URL
    2. Transcribe: Convert audio to text using Whisper
    3. Analyze: Summarize transcript using Claude AI

    Supports progress reporting at each stage.
    """

    def __init__(self, progress_callback=None):
        """
        Initialize pipeline.

        Args:
            progress_callback (ProgressCallback, optional): Callback for progress updates
        """
        self.progress_callback = progress_callback
        self.downloader = Downloader(progress_callback)
        self.transcriber = Transcriber(progress_callback)
        self.analyzer = Analyzer(progress_callback)

    def run(self, url, output_dir, auth_config, endpoint=None, device='cpu',
            model_size='base', no_auth=False):
        """
        Run full pipeline: download → transcribe → analyze.

        Args:
            url (str): Video/audio URL to download
            output_dir (str): Output directory for all files
            auth_config (dict): Authentication config for analyzer
                - method: 'aws' or 'direct'
                - For 'aws': secret_name, region_name
                - For 'direct': api_key
            endpoint (str, optional): Custom API endpoint for analyzer
            device (str): Transcription device ('cpu' or 'cuda')
            model_size (str): Whisper model size
            no_auth (bool): Skip authentication for download

        Returns:
            tuple: (success: bool, results: dict, message: str)
            results dict contains: {'video': path, 'transcript': path, 'analysis': path}
        """
        results = {}

        try:
            # Stage 1: Download
            self._log("=" * 60, "info")
            self._log("STAGE 1/3: DOWNLOADING", "info")
            self._log("=" * 60, "info")

            success, video_file, msg = self.downloader.download(
                url=url,
                output_dir=output_dir,
                no_auth=no_auth
            )

            if not success:
                error_msg = f"Download failed: {msg}"
                self._log(error_msg, "error")
                return False, results, error_msg

            results['video'] = video_file
            self._log(f"✓ Download complete: {video_file}", "info")

            # Stage 2: Transcribe
            self._log("\n" + "=" * 60, "info")
            self._log("STAGE 2/3: TRANSCRIBING", "info")
            self._log("=" * 60, "info")

            success, transcript_file, msg = self.transcriber.transcribe(
                audio_file=video_file,
                output_dir=output_dir,
                device=device,
                model_size=model_size
            )

            if not success:
                error_msg = f"Transcription failed: {msg}"
                self._log(error_msg, "error")
                return False, results, error_msg

            results['transcript'] = transcript_file
            self._log(f"✓ Transcription complete: {transcript_file}", "info")

            # Stage 3: Analyze
            self._log("\n" + "=" * 60, "info")
            self._log("STAGE 3/3: ANALYZING", "info")
            self._log("=" * 60, "info")

            # Get API key via auth manager
            try:
                api_key = AuthManager.get_api_key(**auth_config)
            except Exception as e:
                error_msg = f"Authentication failed: {str(e)}"
                self._log(error_msg, "error")
                return False, results, error_msg

            success, analysis_file, msg = self.analyzer.analyze(
                transcript_file=transcript_file,
                output_dir=output_dir,
                api_key=api_key,
                endpoint=endpoint
            )

            if not success:
                error_msg = f"Analysis failed: {msg}"
                self._log(error_msg, "error")
                return False, results, error_msg

            results['analysis'] = analysis_file
            self._log(f"✓ Analysis complete: {analysis_file}", "info")

            # Pipeline complete
            self._log("\n" + "=" * 60, "info")
            self._log("PIPELINE COMPLETE", "info")
            self._log("=" * 60, "info")
            self._log(f"Video: {results['video']}", "info")
            self._log(f"Transcript: {results['transcript']}", "info")
            self._log(f"Analysis: {results['analysis']}", "info")

            return True, results, "Pipeline completed successfully"

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            self._log(error_msg, "error")
            if self.progress_callback:
                self.progress_callback.error(error_msg, e)
            return False, results, error_msg

    def _log(self, message, level='info'):
        """Send log message via callback or print."""
        if self.progress_callback:
            self.progress_callback.log(message, level)
        else:
            print(f"[{level.upper()}] {message}")
