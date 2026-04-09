# Downloading Videos from Intranet Sites (e.g., myeq.equiniti.com)

## The Problem with Blob URLs

If you see a URL like `blob:https://myeq.equiniti.com/8b02369c-54cd-4cac-aee6-f010d2034dd6`, this is a **blob URL** - it only exists in your browser's memory and **cannot be downloaded directly**.

## How to Get the Real Video URL

### Method 1: Browser Developer Tools (Network Tab)

1. **Open the page** with the video in Chrome/Edge
2. **Press F12** to open Developer Tools
3. **Go to Network tab**
4. **Filter by "media" or "mp4"** (at the top of Network tab)
5. **Play the video** or refresh the page
6. **Look for the actual video file** (usually a .mp4, .webm, or .m3u8 file)
7. **Right-click the file** → Copy → Copy URL

This gives you the REAL URL behind the blob URL.

### Method 2: Inspect the Video Element

1. **Right-click the video** → Inspect
2. Look for `<video>` or `<source>` tags in the HTML
3. Check for a `src` attribute with the real URL
4. If you see blob URL, look for JavaScript code that creates it

### Method 3: Check Page Source for URLs

1. **Right-click the page** → View Page Source
2. **Search for** (Ctrl+F):
   - `.mp4`
   - `.webm`
   - `video`
   - `https://` (look for domain-specific URLs)

## Authentication Required

Intranet sites require your browser's authentication. You need to:

### Step 1: Export Your Browser Cookies

**Using Cookie-Editor Extension (Recommended):**

1. Install [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) for Chrome
2. Open your intranet site (e.g., `https://myeq.equiniti.com`)
3. Click the Cookie-Editor icon in the toolbar
4. Click **Export** → Save as `intranet_cookies.json`

**Manual Method:**

1. Open your intranet site
2. Press **F12** → **Application** tab → **Cookies**
3. Copy all cookies into a JSON file:

```json
{
  "sessionid": "your-session-id",
  "auth_token": "your-auth-token",
  "_ga": "GA1.2.123456789.1234567890"
}
```

### Step 2: Export Request Headers (Optional but Recommended)

Sometimes you need additional headers:

1. **F12** → **Network** tab
2. **Refresh the page**
3. **Click any request** to your intranet domain
4. **Copy Request Headers** → save as `intranet_headers.json`:

```json
{
  "User-Agent": "Mozilla/5.0...",
  "Authorization": "Bearer your-token-if-present",
  "X-Custom-Header": "value"
}
```

## Using the Downloader with Intranet URLs

Once you have the real URL (not blob URL) and cookies:

### GUI Method:

```python
# Run gui_simple_download.py
# Paste the REAL URL (not blob URL)
# Make sure cookies/headers are in the project folder
# Uncheck "Skip authentication" checkbox
# Download
```

### Command Line Method:

```python
from core.downloader import Downloader

downloader = Downloader()
success, output_file, message = downloader.download(
    url="https://myeq.equiniti.com/actual/video/path.mp4",  # Real URL, not blob!
    output_dir="dump/1",
    cookies_file="intranet_cookies.json",
    headers_file="intranet_headers.json",
    no_auth=False
)
```

## Common Issues

### 403 Forbidden (Like Your Error)

**Causes:**
- Missing authentication cookies
- Wrong/expired session tokens
- Corporate proxy (Zscaler) blocking the request
- IP address restrictions

**Solutions:**
1. Export fresh cookies while logged into the site
2. Make sure you're on the same network (VPN if working remotely)
3. Check if the video URL has an expiration timestamp
4. Try accessing the URL in a private/incognito browser - if it fails, you need auth

### 404 Not Found

**Causes:**
- The blob URL was used instead of real URL
- Video URL has expired (temporary signed URLs)

**Solutions:**
1. Find the real URL using Network tab
2. Generate a new video link from the intranet portal

### Corporate Proxy Issues (Zscaler)

If your company uses Zscaler (like shown in your error):

1. The proxy might require specific certificates
2. Some tools may need proxy configuration
3. Contact IT if videos are blocked by policy

## Example: Your Case

Your error showed:
```
Response status: 403
Server: Zscaler/6.2
```

This means:
1. ✗ You tried to download a non-blob URL (good!)
2. ✗ But Zscaler blocked it due to missing authentication
3. ✗ The downloader sent wrong headers (Zoom-specific ones)

**To fix:**
1. Export cookies from `myeq.equiniti.com` while logged in
2. Find the real video URL using Network tab
3. The downloader will auto-detect the domain and use appropriate headers

## Testing Your Setup

Quick test to verify cookies work:

```python
import requests
import json

# Load your cookies
with open('intranet_cookies.json', 'r') as f:
    cookies = json.load(f)

# Test request
response = requests.get(
    'https://myeq.equiniti.com/your-video-url',
    cookies=cookies,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://myeq.equiniti.com/'
    }
)

print(f"Status: {response.status_code}")
print(f"Content type: {response.headers.get('Content-Type')}")
```

If you get status 200 and content-type is video, you're good to go!
