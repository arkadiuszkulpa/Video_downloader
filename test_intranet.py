"""
Test script to check if intranet authentication is working.

This helps you verify that your exported cookies/headers work
before trying to download the actual video.
"""

import requests
import json
import os


def test_intranet_auth(url, cookies_file=None, headers_file=None):
    """
    Test if authentication works for an intranet URL.
    
    Args:
        url (str): The intranet URL to test
        cookies_file (str): Path to cookies JSON file
        headers_file (str): Path to headers JSON file
    """
    print(f"Testing access to: {url}\n")
    
    # Load cookies if provided
    cookies = {}
    if cookies_file and os.path.exists(cookies_file):
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        print(f"✓ Loaded {len(cookies)} cookies from {cookies_file}")
    else:
        print("⚠ No cookies file provided or file not found")
    
    # Load headers if provided
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
    }
    if headers_file and os.path.exists(headers_file):
        with open(headers_file, 'r') as f:
            headers.update(json.load(f))
        print(f"✓ Loaded custom headers from {headers_file}")
    
    # Add domain-appropriate referer
    from urllib.parse import urlparse
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    headers.update({"Referer": f"{base_url}/"})
    
    print(f"\nSending request...")
    print(f"Headers: {list(headers.keys())}")
    print(f"Cookies: {list(cookies.keys())}\n")
    
    # Make request
    try:
        response = requests.get(
            url,
            headers=headers,
            cookies=cookies,
            stream=True,
            timeout=10,
            verify=False,
            allow_redirects=True
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"Content-Length: {response.headers.get('Content-Length', 'unknown')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'video' in content_type or 'octet-stream' in content_type:
                print("\n✓ SUCCESS! Authentication works and this looks like a video file.")
                print("  You should be able to download this URL.")
            elif 'html' in content_type:
                print("\n⚠ WARNING: Got HTML instead of video.")
                print("  This might be a login page or error page.")
                print(f"  First 500 chars of response:\n{response.text[:500]}")
            else:
                print(f"\n? Got unexpected content type: {content_type}")
        elif response.status_code == 403:
            print("\n✗ FORBIDDEN (403)")
            print("  Authentication failed or cookies are missing/expired.")
            print("  Try exporting fresh cookies while logged into the site.")
        elif response.status_code == 404:
            print("\n✗ NOT FOUND (404)")
            print("  The URL doesn't exist or has expired.")
        else:
            print(f"\n✗ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")


def find_video_url_instructions():
    """Print instructions for finding the real video URL."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           HOW TO FIND THE REAL VIDEO URL (NOT BLOB URL)        ║
╚════════════════════════════════════════════════════════════════╝

If you see a blob: URL, follow these steps:

1. Open the intranet page with the video in Chrome/Edge
2. Press F12 to open Developer Tools
3. Click the "Network" tab
4. Filter by "media" or "mp4" (at the top)
5. Play the video or refresh the page
6. Look for the actual video file (e.g., .mp4, .webm, .m3u8)
7. Right-click the file → Copy → Copy URL

That's your REAL URL to use for downloading!

Example of what you're looking for:
  ✓ https://myeq.equiniti.com/storage/videos/training-2024.mp4
  ✗ blob:https://myeq.equiniti.com/8b02369c-54cd-4cac-aee6-...

╔════════════════════════════════════════════════════════════════╗
║              HOW TO EXPORT BROWSER COOKIES                      ║
╚════════════════════════════════════════════════════════════════╝

Method 1: Cookie-Editor Extension (Easiest)
  1. Install Cookie-Editor from Chrome Web Store
  2. Open your intranet site (while logged in!)
  3. Click Cookie-Editor icon
  4. Click "Export" → Save as JSON
  5. Save as "intranet_cookies.json" in this folder

Method 2: Manual (DevTools)
  1. Open your intranet site
  2. F12 → Application → Cookies
  3. Copy all cookie names and values
  4. Create a JSON file like:
     {
       "sessionid": "abc123...",
       "auth_token": "def456..."
     }

""")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║          INTRANET VIDEO DOWNLOAD - AUTHENTICATION TEST          ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Check if user needs instructions
    import sys
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h', 'help']:
        find_video_url_instructions()
        
        print("\nUsage:")
        print("  python test_intranet.py <url> [cookies_file] [headers_file]")
        print("\nExample:")
        print("  python test_intranet.py https://myeq.equiniti.com/video.mp4 intranet_cookies.json")
        print("")
        sys.exit(0)
    
    # Get arguments
    url = sys.argv[1]
    cookies_file = sys.argv[2] if len(sys.argv) > 2 else None
    headers_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Run test
    test_intranet_auth(url, cookies_file, headers_file)
    
    print("\n" + "="*70)
    print("TIP: If authentication fails, see INTRANET_DOWNLOAD_GUIDE.md")
    print("="*70)
