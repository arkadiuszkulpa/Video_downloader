"""Video/audio downloader with progress callback support."""

import requests
import os
import json
import subprocess
from datetime import datetime
from urllib.parse import urlparse, unquote


# Default headers for authenticated downloads
DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-encoding": "identity;q=1, *;q=0",
    "accept-language": "en-GB,en;q=0.9",
    "referer": "https://instytutkryptografii.pl/",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "video",
    "sec-fetch-mode": "no-cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
}

DEFAULT_COOKIES = {
    "_gcl_au": "1.1.1469172500.1756223364",
    "_clck": "22z37h^2^fys^0^2064",
    "_fbp": "fb.1.1756223364404.841153882121408119",
    "_tt_enable_cookie": "1",
    "_ttp": "01K3KH3QFYPQ9VHA6FJRHB2F3E_.tt.1",
    "_clsk": "y8a16e^1756223365003^1^1^l.clarity.ms/collect",
    "_rdt_uuid": "1756223364386.6f1bd919-07d1-48ab-b0d6-ac06f9d6d13c",
    "ttcsid": "1756223364609::WEtoDf_bfWr9sLUa24gG.1.1756223883421",
    "ttcsid_CVIMF5BC77U1CRGDMDK0": "1756223364609::cttEkddUIMCE9lPVZ4zB.1.1756223957781",
}


class Downloader:
    """
    Video/audio downloader with resume support and progress callbacks.

    Supports:
    - Resume interrupted downloads
    - Progress reporting via callbacks
    - Custom headers and cookies
    - Automatic file type detection
    - MP4 optimization for seeking
    """

    def __init__(self, progress_callback=None):
        """
        Initialize downloader.

        Args:
            progress_callback (ProgressCallback, optional): Callback for progress updates
        """
        self.progress_callback = progress_callback

    def download(self, url, output_dir, headers_file=None, cookies_file=None, no_auth=False):
        """
        Download video or audio file with progress tracking.

        Args:
            url (str): URL to download
            output_dir (str): Output directory path
            headers_file (str, optional): Path to JSON file with custom headers
            cookies_file (str, optional): Path to JSON file with custom cookies
            no_auth (bool): Skip default headers/cookies for public URLs

        Returns:
            tuple: (success: bool, output_file: str, message: str)
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Prepare headers and cookies
            if no_auth:
                headers = {"User-Agent": "Mozilla/5.0"}
                cookies = {}
                self._log("Using minimal headers (no authentication)", "info")
            else:
                headers = DEFAULT_HEADERS.copy()
                cookies = DEFAULT_COOKIES.copy()

                if headers_file:
                    with open(headers_file, 'r') as f:
                        headers.update(json.load(f))
                    self._log(f"Loaded custom headers from {headers_file}", "info")

                if cookies_file:
                    with open(cookies_file, 'r') as f:
                        cookies.update(json.load(f))
                    self._log(f"Loaded custom cookies from {cookies_file}", "info")

            # Detect file type
            file_type = self._detect_file_type(url)
            self._log(f"Detected file type: {file_type}", "info")

            # Generate unique output filename
            output_file = self._generate_output_filename(url, file_type, output_dir)
            self._log(f"Output file: {output_file}", "info")

            # Download file
            download_success = self._download_with_resume(
                url, output_file, headers, cookies
            )

            if not download_success:
                return False, "", "Download failed"

            # Post-process video files
            if file_type == 'video':
                self._log("Optimizing video for seeking...", "info")
                base_name = os.path.splitext(output_file)[0]
                fixed_file = f"{base_name}_fixed.mp4"

                if self._fix_mp4(output_file, fixed_file):
                    self._log(f"Video optimized: {fixed_file}", "info")
                    return True, fixed_file, "Download and optimization complete"
                else:
                    self._log("Video optimization failed, using original file", "warning")
                    return True, output_file, "Download complete (optimization failed)"
            else:
                self._log(f"Audio file ready: {output_file}", "info")
                return True, output_file, "Download complete"

        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            self._log(error_msg, "error")
            if self.progress_callback:
                self.progress_callback.error(error_msg, e)
            return False, "", error_msg

    def _detect_file_type(self, url):
        """Detect if URL is audio or video based on extension."""
        url_lower = url.lower()
        if url_lower.endswith(('.mp3', '.m4a', '.wav', '.aac', '.flac', '.ogg')):
            return 'audio'
        if url_lower.endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv')):
            return 'video'
        return 'video'  # Default

    def _extract_filename_from_url(self, url):
        """Extract filename from URL, handling URL encoding."""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        filename = unquote(filename)
        return filename if filename else None

    def _generate_output_filename(self, url, file_type, output_dir):
        """Generate unique output filename with timestamp."""
        original_name = self._extract_filename_from_url(url)

        if original_name:
            name_without_ext, ext = os.path.splitext(original_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name_without_ext}_{timestamp}{ext}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if file_type == 'audio':
                filename = f"audio_{timestamp}.mp3"
            else:
                filename = f"video_{timestamp}.mp4"

        return os.path.join(output_dir, filename)

    def _download_with_resume(self, url, output, headers, cookies, chunk_size=8*1024*1024):
        """
        Download file with resume support and progress reporting.

        Args:
            url (str): Download URL
            output (str): Output file path
            headers (dict): HTTP headers
            cookies (dict): HTTP cookies
            chunk_size (int): Download chunk size (default: 8MB)

        Returns:
            bool: True if download successful
        """
        try:
            # Get file size
            size = self._get_file_size(url, headers, cookies)
            self._log(f"File size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)", "info")

            # Check for existing partial download
            downloaded = 0
            if os.path.exists(output):
                downloaded = os.path.getsize(output)
                self._log(f"Resuming from {downloaded:,} bytes", "info")

            mode = "ab" if downloaded > 0 else "wb"

            with open(output, mode) as f:
                while downloaded < size:
                    end = min(downloaded + chunk_size - 1, size - 1)
                    range_headers = headers.copy()
                    range_headers["Range"] = f"bytes={downloaded}-{end}"

                    resp = requests.get(url, headers=range_headers, cookies=cookies,
                                        stream=True, timeout=30)

                    if resp.status_code in (200, 206):
                        for chunk in resp.iter_content(512*1024):  # 512KB buffer
                            if chunk:
                                f.write(chunk)

                        downloaded = end + 1

                        # Update progress
                        percent = (downloaded / size * 100) if size > 0 else 0
                        speed_mb = chunk_size / 1024 / 1024  # Rough estimate
                        message = f"Downloaded {downloaded:,}/{size:,} bytes ({percent:.1f}%) - ~{speed_mb:.1f} MB/chunk"

                        if self.progress_callback:
                            self.progress_callback.update('download', downloaded, size, message)
                        else:
                            print(f"\r{message}", end="")

                    elif resp.status_code == 403:
                        self._log("Access forbidden (403). Retrying...", "warning")
                        continue
                    else:
                        self._log(f"Failed with status {resp.status_code}", "error")
                        return False

            if not self.progress_callback:
                print()  # Newline after progress

            self._log("Download complete", "info")
            return True

        except Exception as e:
            self._log(f"Resume download failed: {e}. Trying fallback method...", "warning")
            return self._download_fallback(url, output, headers, cookies)

    def _get_file_size(self, url, headers, cookies):
        """Get file size using range request."""
        range_headers = headers.copy()
        range_headers["Range"] = "bytes=0-"
        resp = requests.get(url, headers=range_headers, cookies=cookies, stream=True)

        if resp.status_code in (200, 206):
            if "Content-Range" in resp.headers:
                cr = resp.headers["Content-Range"]
                return int(cr.split("/")[-1])
            elif "Content-Length" in resp.headers:
                return int(resp.headers["Content-Length"])

        raise Exception("Could not determine file size")

    def _download_fallback(self, url, output, headers, cookies):
        """Fallback download method without resume support."""
        try:
            self._log("Using fallback download method (no resume support)", "info")
            resp = requests.get(url, headers=headers, cookies=cookies, stream=True, timeout=30)

            with open(output, "wb") as f:
                for chunk in resp.iter_content(1024*64):
                    if chunk:
                        f.write(chunk)

            self._log("Download complete (fallback mode)", "info")
            return True

        except Exception as e:
            self._log(f"Fallback download failed: {e}", "error")
            return False

    def _fix_mp4(self, input_file, output_file):
        """
        Optimize MP4 file for seeking using FFmpeg.

        Args:
            input_file (str): Input MP4 path
            output_file (str): Output optimized MP4 path

        Returns:
            bool: True if optimization successful
        """
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", input_file,
                "-c", "copy", "-movflags", "faststart",
                output_file
            ], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}", "error")
            return False
        except FileNotFoundError:
            self._log("FFmpeg not found. Install FFmpeg to enable video optimization.", "error")
            return False

    def _log(self, message, level='info'):
        """Send log message via callback or print."""
        if self.progress_callback:
            self.progress_callback.log(message, level)
        else:
            print(f"[{level.upper()}] {message}")
