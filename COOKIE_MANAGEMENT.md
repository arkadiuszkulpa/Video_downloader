# Cookie Management Summary

## What You Have Now

✓ **zoom_cookies.json** - Contains your current Zoom session cookies
✓ **Auto-loading** - Downloader automatically uses these cookies for Zoom URLs
✓ **update_zoom_cookies.py** - Interactive script to refresh cookies

## How Cookies Work

**Static File Approach:**
- Cookies are stored in `zoom_cookies.json`
- The downloader reads from this file (does NOT auto-grab from browser)
- When cookies expire, you must manually update the file

**Why Not Auto-Grab from Browser?**
- Browser cookies are stored in encrypted databases
- Would require browser-specific code for Chrome/Edge/Firefox
- Your org blocks browser extensions that could do this
- Static file approach is simpler and more reliable

## When Cookies Expire

**Symptoms:**
- Downloads fail with 403 Forbidden
- Error message tells you to update cookies

**How Long Do Cookies Last?**
- Session cookies (`_zm_ssid`, `_zm_page_auth`) - expire when you log out or close browser
- Persistent cookies (`cf_clearance`, `_zm_visitor_guid`) - days/weeks/months
- Most Zoom tokens last until you explicitly log out

**Best Practice:**
- Keep your Zoom session open in browser
- Only update cookies when you get 403 errors
- Typically need updating every few days/weeks

## How to Update Cookies

### Option 1: Use the Helper Script (Easiest)
```powershell
conda activate py3.11
python update_zoom_cookies.py
```
Follow the prompts and paste new cookie values from DevTools.

### Option 2: Manual Update
1. F12 in Chrome → Application → Cookies → arden-ac-uk.zoom.us
2. Copy cookie values
3. Edit `zoom_cookies.json` directly

### Key Cookies to Update
Priority order (update these first):
1. `_zm_ssid` - Session ID (most important)
2. `_zm_page_auth` - Page authentication
3. `cf_clearance` - Cloudflare clearance  
4. `cred` - Credentials
5. `__cf_bm` - Cloudflare bot management

## Alternative: Browser Developer Tools Network Tab

Instead of managing cookies, you can also:
1. Play the video in browser
2. F12 → Network tab → filter by "mp4"
3. Find the video request → Copy → Copy as cURL
4. Use that cURL command directly (includes all headers/cookies)

This gets a one-time download URL but avoids cookie management.

## Future Enhancement Ideas

If cookie updates become too frequent/annoying:
- Could create a browser bookmarklet to export cookies as JSON
- Could use Selenium to auto-launch browser and grab cookies
- Could integrate with password managers that store cookies

For now, the manual update approach works and is most reliable.
