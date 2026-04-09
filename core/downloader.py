"""Video/audio downloader with progress callback support."""

import requests
import os
import json
import subprocess
from datetime import datetime
from urllib.parse import urlparse, unquote
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
            # Check for blob URLs
            if url.startswith('blob:'):
                error_msg = (
                    "Cannot download blob URLs directly. "
                    "Blob URLs only exist in your browser's memory. "
                    "Please see INTRANET_DOWNLOAD_GUIDE.md for instructions on finding the real video URL."
                )
                self._log(error_msg, "error")
                return False, "", error_msg

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Prepare headers and cookies - use domain-specific defaults
            headers = self._get_default_headers(url, no_auth)
            cookies = {}

            # Auto-detect Zoom and load cookies if available
            parsed_url = urlparse(url)
            is_zoom = 'zoom.us' in parsed_url.netloc.lower()
            
            # Load custom headers/cookies if provided
            if headers_file and not no_auth:
                with open(headers_file, 'r') as f:
                    headers.update(json.load(f))
                self._log(f"Loaded custom headers from {headers_file}", "info")

            if cookies_file and not no_auth:
                with open(cookies_file, 'r') as f:
                    cookies.update(json.load(f))
                self._log(f"Loaded custom cookies from {cookies_file}", "info")
            elif is_zoom and not no_auth:
                # Try to auto-load zoom_cookies.json for Zoom URLs
                zoom_cookies_path = os.path.join(os.path.dirname(__file__), '..', 'zoom_cookies.json')
                if os.path.exists(zoom_cookies_path):
                    with open(zoom_cookies_path, 'r') as f:
                        cookies.update(json.load(f))
                    self._log("Auto-loaded zoom_cookies.json for Zoom URL", "info")
                else:
                    self._log("Zoom URL detected but zoom_cookies.json not found in project root", "warning")

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

    def _get_default_headers(self, url, no_auth=False):
        """
        Get domain-appropriate default headers.
        
        Args:
            url (str): URL being downloaded
            no_auth (bool): Skip domain-specific headers
            
        Returns:
            dict: Default headers appropriate for the domain
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Base headers for all requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        if no_auth:
            return headers
            
        # Domain-specific headers
        if 'zoom.us' in domain:
            headers.update({
                "Referer": "https://ssrweb.zoom.us/",
                "Origin": "https://ssrweb.zoom.us"
            })
            self._log("Using Zoom-specific headers", "debug")
        else:
            # For intranet or other sites, use the site's own domain as referer
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            headers.update({
                "Referer": f"{base_url}/",
            })
            self._log(f"Using domain-specific headers for {domain}", "debug")
            
        return headers

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
                                        stream=True, timeout=30, verify=False, allow_redirects=True)

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
        resp = requests.get(url, headers=range_headers, cookies=cookies, stream=True, verify=False, allow_redirects=True)

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
            resp = requests.get(url, headers=headers, cookies=cookies, stream=True, timeout=30, verify=False, allow_redirects=True)
            
            self._log(f"Final URL after redirects: {resp.url}", "info")
            self._log(f"Response status: {resp.status_code}", "info")
            self._log(f"Response headers: {dict(resp.headers)}", "info")
            
            # Check if request was successful
            if resp.status_code == 403:
                parsed_url = urlparse(url)
                is_zoom = 'zoom.us' in parsed_url.netloc.lower()
                
                self._log(f"Download failed with status code: 403 (Forbidden)", "error")
                
                if is_zoom:
                    self._log("╔════════════════════════════════════════════════════════════╗", "error")
                    self._log("║ Your Zoom session cookies have likely EXPIRED             ║", "error")
                    self._log("║                                                            ║", "error")
                    self._log("║ TO FIX:                                                    ║", "error")
                    self._log("║   1. Run: python update_zoom_cookies.py                   ║", "error")
                    self._log("║   2. Follow prompts to update cookies from your browser   ║", "error")
                    self._log("║   3. Try downloading again                                ║", "error")
                    self._log("║                                                            ║", "error")
                    self._log("║ See ZOOM_DOWNLOAD_GUIDE.md for detailed instructions      ║", "error")
                    self._log("╚════════════════════════════════════════════════════════════╝", "error")
                else:
                    self._log("This usually means authentication is required.", "error")
                    self._log("Please export cookies from your browser. See INTRANET_DOWNLOAD_GUIDE.md", "error")
                
                # Try to read response body for error details
                try:
                    error_body = resp.text[:1000]
                    if error_body:
                        self._log(f"Response body: {error_body}", "error")
                except:
                    pass
                return False
            elif resp.status_code != 200:
                self._log(f"Download failed with status code: {resp.status_code}", "error")
                # Try to read response body for error details
                try:
                    error_body = resp.text[:1000]
                    if error_body:
                        self._log(f"Response body: {error_body}", "error")
                except:
                    pass
                return False
            
            # Get file size if available
            total_size = int(resp.headers.get('content-length', 0))
            if total_size > 0:
                self._log(f"File size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)", "info")
            else:
                self._log("File size unknown, downloading...", "info")
            
            downloaded = 0
            with open(output, "wb") as f:
                for chunk in resp.iter_content(1024*64):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        if total_size > 0:
                            percent = (downloaded / total_size * 100)
                            message = f"Downloaded {downloaded:,}/{total_size:,} bytes ({percent:.1f}%)"
                            if self.progress_callback:
                                self.progress_callback.update('download', downloaded, total_size, message)
                        elif downloaded % (1024*1024*10) == 0:  # Log every 10MB if size unknown
                            self._log(f"Downloaded {downloaded:,} bytes ({downloaded / 1024 / 1024:.2f} MB)...", "info")

            self._log(f"Download complete (fallback mode): {downloaded:,} bytes", "info")
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
