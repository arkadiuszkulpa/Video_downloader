# Manual Cookie Conversion Guide

## Understanding the Chrome DevTools Cookie Format

When you copy cookies from Chrome DevTools, you get **tab-separated** text like this:

```
__cf_bm	VALUE_HERE	.zoom.us	/	2026-03-09T10:50:38.343Z	177	✓	✓	None	Medium
_zm_ssid	ANOTHER_VALUE	.zoom.us	/	Session	36	✓	✓		Medium
```

### Column Structure (separated by TAB characters):
1. **Name** - Cookie name (e.g., `__cf_bm`)
2. **Value** - Cookie value (e.g., `VALUE_HERE`) ← **This is what we need!**
3. Domain - e.g., `.zoom.us` (ignore)
4. Path - e.g., `/` (ignore)
5. Expires - e.g., `2026-03-09...` (ignore)
6. Size - e.g., `177` (ignore)
7. HttpOnly - `✓` or blank (ignore)
8. Secure - `✓` or blank (ignore)
9. SameSite - `None`, `Lax`, etc. (ignore)
10. Priority - `Medium`, etc. (ignore)

**WE ONLY NEED COLUMNS 1 AND 2!**

## The Simple Rule

```
Column 1 (Name) → JSON key
Column 2 (Value) → JSON value
Everything else → IGNORE
```

## Converting to JSON - Three Methods

### Method 1: Use the Parser Script (Easiest!)

```powershell
python parse_cookies.py
```

1. Copy ALL cookies from DevTools (Ctrl+A, Ctrl+C)
2. Run the script
3. Paste when prompted
4. Press Enter on blank line
5. Done! JSON file is created

### Method 2: Manual with Text Editor

If the parser doesn't work, use any text editor:

**Step 1: Copy cookies from Chrome to a text file**

Raw data looks like:
```
__cf_bm	ABC123...	.zoom.us	/	2026-03-09...	177	✓	✓	None	Medium
_zm_ssid	XYZ789...	.zoom.us	/	Session	36	✓	✓		Medium
cred	DEF456...	.zoom.us	/	Session	36	✓	✓		Medium
```

**Step 2: Extract Name and Value (columns 1 and 2)**

You need:
```
__cf_bm → ABC123...
_zm_ssid → XYZ789...
cred → DEF456...
```

**Step 3: Convert to JSON format**

```json
{
    "__cf_bm": "ABC123...",
    "_zm_ssid": "XYZ789...",
    "cred": "DEF456..."
}
```

**JSON Rules:**
- Start with `{` and end with `}`
- Each cookie: `"name": "value"`
- Separate with commas (except last one)
- Use double quotes `"` not single quotes `'`

**Step 4: Save as `zoom_cookies.json`**

### Method 3: Excel/Spreadsheet (If you prefer)

1. Paste cookie data into Excel
2. Column A = Name, Column B = Value
3. Delete columns C onwards (domain, path, etc.)
4. Export to CSV
5. Convert CSV to JSON (or use the parser on the CSV)

## Quick Reference: JSON Format

```json
{
    "cookie_name_1": "cookie_value_1",
    "cookie_name_2": "cookie_value_2",
    "cookie_name_3": "cookie_value_3"
}
```

**Key points:**
- Curly braces: `{ }` around everything
- Each entry: `"name": "value"`
- Comma after each entry except the last
- Use double quotes `"`
- Indent for readability (optional but nice)

## Common Mistakes

❌ **Missing comma:**
```json
{
    "cookie1": "value1"    ← Missing comma!
    "cookie2": "value2"
}
```

✓ **Correct:**
```json
{
    "cookie1": "value1",   ← Comma here
    "cookie2": "value2"    ← No comma on last one
}
```

❌ **Single quotes:**
```json
{
    'cookie1': 'value1'    ← Wrong quotes!
}
```

✓ **Correct:**
```json
{
    "cookie1": "value1"    ← Double quotes
}
```

❌ **Forgot to remove extra columns:**
```json
{
    "__cf_bm": "ABC123... .zoom.us / 2026-03-09..."    ← Has domain/path/expiry!
}
```

✓ **Correct:**
```json
{
    "__cf_bm": "ABC123..."    ← Only the value
}
```

## Testing Your JSON

After creating the file, test it's valid:

```powershell
python -c "import json; print('Valid!' if json.load(open('zoom_cookies.json')) else 'Invalid')"
```

Or just try a download - if it works, your JSON is correct!

## When in Doubt

Just use the parser script:
```powershell
python parse_cookies.py
```

It handles all the formatting for you!
