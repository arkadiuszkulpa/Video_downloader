"""
Helper script to update Zoom cookies.

When you get 403 errors again, your cookies have expired. Follow these steps:

1. Open Chrome/Edge and go to https://arden-ac-uk.zoom.us
2. Press F12 to open DevTools
3. Go to Application tab → Cookies → expand the Zoom domain
4. Run this script
5. When prompted, paste each cookie value (or press Enter to skip)
"""

import json
import os

COOKIES_FILE = "zoom_cookies.json"

# Common Zoom cookies that need to be updated
COOKIE_NAMES = [
    "__cf_bm",
    "_zm_ssid",
    "_zm_page_auth",
    "_zm_ctaid",
    "_zm_csp_script_nonce",
    "cred",
    "cf_clearance",
    "_zm_join_utid"
]

print("=" * 60)
print("ZOOM COOKIES UPDATER")
print("=" * 60)
print("\n1. Open Chrome and go to your Zoom site")
print("2. Press F12 → Application → Cookies → (your zoom domain)")
print("3. Find these cookies and paste their values below:\n")

# Load existing cookies if available
if os.path.exists(COOKIES_FILE):
    with open(COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    print(f"✓ Found existing {COOKIES_FILE}\n")
else:
    cookies = {}
    print(f"Creating new {COOKIES_FILE}\n")

# Ask for important cookies
updated = False
for cookie_name in COOKIE_NAMES:
    current_value = cookies.get(cookie_name, "")
    if current_value:
        print(f"\n{cookie_name}:")
        print(f"  Current: {current_value[:50]}..." if len(current_value) > 50 else f"  Current: {current_value}")
    else:
        print(f"\n{cookie_name}: (new)")
    
    new_value = input(f"  Enter new value (or press Enter to keep current): ").strip()
    
    if new_value:
        cookies[cookie_name] = new_value
        updated = True
        print("  ✓ Updated")
    elif current_value:
        print("  ✓ Keeping current value")
    else:
        print("  ⚠ Skipped (no value)")

# Option to add other cookies
print("\n" + "-" * 60)
add_more = input("\nAdd more cookies? (y/n): ").lower().strip()

while add_more == 'y':
    name = input("Cookie name: ").strip()
    if name:
        value = input(f"Value for {name}: ").strip()
        if value:
            cookies[name] = value
            updated = True
            print("  ✓ Added")
    
    add_more = input("\nAdd another? (y/n): ").lower().strip()

# Save cookies
if updated or not os.path.exists(COOKIES_FILE):
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies, f, indent=4)
    print(f"\n✓ Saved to {COOKIES_FILE}")
    print(f"✓ Total cookies: {len(cookies)}")
else:
    print("\n⚠ No changes made")

print("\n" + "=" * 60)
print("Done! Your Zoom downloads should work now.")
print("=" * 60)
