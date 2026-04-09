# Browser Download Test

## Step 1: Test if the link works
1. Copy your Zoom recording URL
2. Paste it in Chrome/Firefox address bar
3. Does it start downloading the video?

## Step 2: If it works, get your browser cookies
If the browser can download it, we need to extract your Zoom cookies:

### Chrome:
1. Go to Zoom in Chrome
2. Press F12 (Developer Tools)
3. Go to Application tab → Cookies → https://ssrweb.zoom.us
4. Copy all cookies and their values

### Alternative: Use browser's download functionality
Instead of Python, you can use `curl` with browser cookies:

```bash
curl -o video.mp4 "YOUR_ZOOM_URL" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://ssrweb.zoom.us/" \
  --cookie "your_cookies_here"
```

## Step 3: Check Your IP
The signed URL might be IP-locked. Check:
1. What IP you had when you got the link
2. What IP you have now when downloading
3. Are you using VPN/proxy that changes IPs?
