"""
Parse cookies from Chrome DevTools and convert to JSON.

USAGE:
1. Chrome → F12 → Application → Cookies → (your zoom domain)
2. Click on the first cookie
3. Press Ctrl+A to select all cookies
4. Press Ctrl+C to copy
5. Run this script
6. Paste the copied data when prompted
7. Press Enter on a blank line when done

The script will create/update zoom_cookies.json automatically.
"""

import json
import os

COOKIES_FILE = "zoom_cookies.json"

def parse_cookie_line(line):
    """
    Parse a tab-separated cookie line from Chrome DevTools.
    
    Format from DevTools:
    Name\tValue\tDomain\tPath\tExpires\tSize\tHttpOnly\tSecure\tSameSite\tPriority
    
    We only need:
    Name (column 1) and Value (column 2)
    """
    parts = line.split('\t')
    
    if len(parts) >= 2:
        name = parts[0].strip()
        value = parts[1].strip()
        
        # Skip empty names or values
        if name and value:
            return name, value
    
    return None, None

def main():
    print("=" * 70)
    print("CHROME DEVTOOLS COOKIE PARSER")
    print("=" * 70)
    print("\nInstructions:")
    print("1. Open Chrome → F12 → Application → Cookies → (zoom domain)")
    print("2. Click inside the cookies table")
    print("3. Press Ctrl+A to select ALL cookies")
    print("4. Press Ctrl+C to copy")
    print("5. Paste below (Ctrl+V) - you'll see multiple lines")
    print("6. Press Enter on a blank line to finish")
    print("\n" + "-" * 70)
    
    # Load existing cookies
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, 'r') as f:
            cookies = json.load(f)
        print(f"✓ Found existing {COOKIES_FILE} - will update it\n")
    else:
        cookies = {}
        print(f"Creating new {COOKIES_FILE}\n")
    
    print("Paste cookie data (press Enter on blank line when done):")
    print("-" * 70)
    
    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)
    
    if not lines:
        print("\n⚠ No data pasted. Exiting.")
        return
    
    # Parse cookies
    new_cookies = {}
    for line in lines:
        name, value = parse_cookie_line(line)
        if name and value:
            new_cookies[name] = value
    
    if not new_cookies:
        print("\n⚠ No valid cookies found in pasted data.")
        print("\nExpected format (tab-separated from Chrome DevTools):")
        print("Name<TAB>Value<TAB>Domain<TAB>...")
        return
    
    # Show what we parsed
    print("\n" + "=" * 70)
    print(f"✓ Parsed {len(new_cookies)} cookies:")
    print("-" * 70)
    for name in sorted(new_cookies.keys()):
        value = new_cookies[name]
        value_preview = value[:50] + "..." if len(value) > 50 else value
        print(f"  {name:30} = {value_preview}")
    
    # Update existing cookies
    cookies.update(new_cookies)
    
    # Save to file
    with open(COOKIES_FILE, 'w') as f:
        json.dump(cookies, f, indent=4)
    
    print("\n" + "=" * 70)
    print(f"✓ Saved {len(cookies)} total cookies to {COOKIES_FILE}")
    print("✓ Your Zoom downloads should work now!")
    print("=" * 70)

if __name__ == "__main__":
    main()
