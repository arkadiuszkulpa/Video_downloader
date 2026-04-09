# Zoom Video Download Guide

## Important: Cookie Expiration

**Your Zoom session cookies will expire!** When you start getting 403 errors again:

### EASIEST METHOD: Use the Cookie Parser

```powershell
python parse_cookies.py
```

1. Chrome → F12 → Application → Cookies → (zoom domain)
2. Click in the cookies table
3. **Ctrl+A** to select all cookies
4. **Ctrl+C** to copy
5. Run the script and **paste** when prompted
6. Press Enter on blank line
7. Done! ✓

The parser automatically converts Chrome's format to JSON.

### Alternative: Interactive Updater

```powershell
python update_zoom_cookies.py
```

This prompts for each important cookie individually (slower but more controlled).

### Manual Method

See [COOKIE_FORMAT_GUIDE.md](COOKIE_FORMAT_GUIDE.md) for how to manually convert DevTools output to JSON.

**Key cookies that usually need updating:**
- `_zm_ssid` (session ID - expires when you log out)
- `_zm_page_auth` (page authentication token)
- `cf_clearance` (Cloudflare clearance)
- `cred` (credentials)

## Using the GUI

1. Run the GUI:
   ```powershell
   conda activate py3.11
   python gui_complete.py
   ```

2. In the **Download** tab:
   - **URL**: Paste your full Zoom recording URL
   - **Output Directory**: Choose where to save (e.g., `dump`)
   - **Skip authentication**: Leave UNCHECKED (so cookies are used)
   - Click **Start Download**

3. The downloader will:
   - Detect it's a Zoom URL
   - Auto-load `zoom_cookies.json`
   - Download the video

## Getting the Zoom URL

1. Go to your Zoom recording in the browser
2. **Right-click on the video player** → "Inspect" (or press F12)
3. Look for `<video>` or `<source>` tag in the Elements panel
4. Find the `src="https://..."` attribute
5. Copy the entire URL (including all the `?` parameters)

## Troubleshooting

### 403 Forbidden Error
- Your cookies have expired
- Update `zoom_cookies.json` with fresh cookies from your browser

### File won't play
- The download was interrupted or corrupted
- Delete the file and try downloading again

### SSL Certificate Error  
- Already fixed! The downloader bypasses SSL verification for corporate proxies

## Example URLs

Zoom URLs look like:
```
https://ssrweb.zoom.us/replay03/2026/02/12/.../file.mp4?response-content-type=...&Policy=...&Signature=...
```

Include the **entire URL** with all parameters!

## Technical Details

The downloader:
- Uses your browser's Zoom session cookies
- Bypasses SSL verification (for corporate networks)
- Shows download progress
- Supports resume (if connection drops)
- Auto-detects file type
- Generates timestamped filenames
