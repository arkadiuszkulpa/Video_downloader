import requests
import os
import argparse
import json
from datetime import datetime
from urllib.parse import urlparse, unquote

HEADERS = {
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

COOKIES = {
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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Download and process video/audio content")
    parser.add_argument('url', help='Video or audio URL to download')
    parser.add_argument('--headers-file', type=str, default=None,
                        help='JSON file with custom headers (optional)')
    parser.add_argument('--cookies-file', type=str, default=None,
                        help='JSON file with custom cookies (optional)')
    parser.add_argument('--output-dir', type=str, default='dump',
                        help='Output directory for files (default: dump)')
    parser.add_argument('--no-auth', action='store_true',
                        help='Skip default headers/cookies for public URLs')
    return parser.parse_args()

def detect_file_type(url, headers_dict=None):
    """Detect if URL is audio or video based on extension or Content-Type"""
    # Check URL extension first
    url_lower = url.lower()
    if url_lower.endswith(('.mp3', '.m4a', '.wav', '.aac', '.flac', '.ogg')):
        return 'audio'
    if url_lower.endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv')):
        return 'video'

    # Check Content-Type from headers if available
    if headers_dict and 'Content-Type' in headers_dict:
        content_type = headers_dict['Content-Type'].lower()
        if 'audio' in content_type:
            return 'audio'
        if 'video' in content_type:
            return 'video'

    # Default to video for backward compatibility
    return 'video'

def extract_filename_from_url(url):
    """Extract filename from URL, handling URL encoding"""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    # Decode URL encoding (e.g., %20 -> space)
    filename = unquote(filename)
    return filename if filename else None

def generate_output_filename(url, file_type, output_dir):
    """Generate unique output filename with timestamp"""
    # Try to extract original filename from URL
    original_name = extract_filename_from_url(url)

    if original_name:
        # Use original filename with timestamp
        name_without_ext, ext = os.path.splitext(original_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name_without_ext}_{timestamp}{ext}"
    else:
        # Fallback to generic name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if file_type == 'audio':
            filename = f"audio_{timestamp}.mp3"
        else:
            filename = f"video_{timestamp}.mp4"

    return os.path.join(output_dir, filename)

def get_video_size(url):
    # Use a range request as in the browser example
    headers = HEADERS.copy()
    headers["Range"] = "bytes=0-"
    resp = requests.get(url, headers=headers, cookies=COOKIES, stream=True)
    print(f"GET status: {resp.status_code}")
    print(f"GET headers: {resp.headers}")
    if resp.status_code in (200, 206):
        if "Content-Range" in resp.headers:
            cr = resp.headers["Content-Range"]
            return int(cr.split("/")[-1])
        elif "Content-Length" in resp.headers:
            return int(resp.headers["Content-Length"])
    raise Exception("Could not determine video size")

def download_video(url, output, chunk_size=8*1024*1024):  # 8MB chunks
    try:
        size = get_video_size(url)
        print(f"Video size: {size} bytes")
        downloaded = 0
        if os.path.exists(output):
            downloaded = os.path.getsize(output)
            print(f"Resuming from {downloaded} bytes")
        mode = "ab" if downloaded > 0 else "wb"
        with open(output, mode) as f:
            while downloaded < size:
                end = min(downloaded + chunk_size - 1, size - 1)
                headers = HEADERS.copy()
                headers["Range"] = f"bytes={downloaded}-{end}"
                resp = requests.get(url, headers=headers, cookies=COOKIES, stream=True, timeout=30)
                if resp.status_code in (200, 206):
                    for chunk in resp.iter_content(512*1024):  # 512KB buffer
                        if chunk:
                            f.write(chunk)
                    downloaded = end + 1
                    print(f"Downloaded {downloaded}/{size} bytes", end="\r")
                elif resp.status_code == 403:
                    print("\nAccess forbidden (403). Retrying...")
                    continue
                else:
                    print(f"\nFailed with status {resp.status_code}")
                    break
        print("\nDownload complete.")
    except Exception as e:
        print(f"Could not determine video size: {e}")
        print("Downloading until EOF (may not support resume)...")
        headers = HEADERS.copy()
        resp = requests.get(url, headers=headers, cookies=COOKIES, stream=True, timeout=30)
        with open(output, "ab") as f:
            for chunk in resp.iter_content(512*1024):
                if chunk:
                    f.write(chunk)
        print("Download complete (EOF mode).")

def fix_mp4(input_file, output_file):
    import subprocess
    print("Fixing MP4 file for seeking...")
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file, "-c", "copy", "-movflags", "faststart", output_file
    ])
    print(f"Fixed file saved as {output_file}")

if __name__ == "__main__":
    args = parse_arguments()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Prepare headers and cookies
    if args.no_auth:
        # For public URLs, use minimal headers
        headers = {"User-Agent": "Mozilla/5.0"}
        cookies = {}
    else:
        # Use defaults, allow override
        headers = HEADERS.copy()
        cookies = COOKIES.copy()

        if args.headers_file:
            with open(args.headers_file, 'r') as f:
                headers.update(json.load(f))

        if args.cookies_file:
            with open(args.cookies_file, 'r') as f:
                cookies.update(json.load(f))

    # Detect file type
    file_type = detect_file_type(args.url)
    print(f"Detected file type: {file_type}")

    # Generate unique output filename with timestamp
    output_file = generate_output_filename(args.url, file_type, args.output_dir)
    print(f"Output file: {output_file}")

    # For video files, also define fixed file path
    if file_type == 'video':
        base_name = os.path.splitext(output_file)[0]
        fixed_file = f"{base_name}_fixed.mp4"
    else:
        print("Audio file detected - will skip video processing")

    try:
        download_video(args.url, output_file)

        # Only process video files
        if file_type == 'video':
            print("Processing video file...")
            fix_mp4(output_file, fixed_file)
        else:
            print(f"Audio file ready at: {output_file}")

    except Exception as e:
        print(f"Download error: {e}")
        print("Attempting fallback download method...")
        resp = requests.get(args.url, headers=headers, cookies=cookies, stream=True)
        with open(output_file, "wb") as f:
            for chunk in resp.iter_content(1024*64):
                if chunk:
                    f.write(chunk)
        print("Download complete (fallback mode).")

        # Only process video files
        if file_type == 'video':
            fix_mp4(output_file, fixed_file)
