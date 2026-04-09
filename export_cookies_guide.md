# How to Export Zoom Cookies from Chrome

The download works in your browser but not in Python because CloudFront needs your Zoom session cookies.

## Method 1: Use Chrome Extension (Easiest)

1. **Install "Cookie-Editor" extension** from Chrome Web Store
   - https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm

2. **Go to Zoom** in Chrome (ssrweb.zoom.us)

3. **Click the Cookie-Editor icon** (cookie icon in toolbar)

4. **Click "Export"** button  

5. **Save as JSON** - save it as `zoom_cookies.json` in your Video_downloader folder

6. **Run download again** with the cookies file

## Method 2: Manual Export from DevTools

1. Open Chrome and go to https://ssrweb.zoom.us
2. Press F12 (open DevTools  
)
3. Go to **Application** tab → **Cookies** → https://ssrweb.zoom.us
4. Copy each cookie and create a JSON file like this:

```json
{
  "cookie_name_1": "value1",
  "cookie_name_2": "value2",  
  "_zm_ssid": "...",
  "_zm_mtk_guid": "...",
  etc...
}
```

## Once you have the cookies file:

The downloader already supports cookies - just need to update the code to use them by default for Zoom URLs.
