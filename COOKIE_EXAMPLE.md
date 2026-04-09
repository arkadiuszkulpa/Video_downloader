# Cookie Conversion Example

## What You Copy from Chrome DevTools

When you select all cookies and copy (Ctrl+A, Ctrl+C), you get this:

```
__cf_bm	.Xwx8a7juu6xJ4IhMFRkzjGqWOpLPxs8ws94UZzOz8Y-1773051638-1.0.1.1-YMYCIqAEXnBBJ7NUqSFwsafsmV.CQCY6.fT9SuV8jwhefQ8LuYFAw5HtTZioknmPyD5mKOG.Rb7ZpyyzEcMSakhOjV7RF2bz23UHkTN3Tz0	.zoom.us	/	2026-03-09T10:50:38.343Z	177	✓	✓	None			Medium
_zm_ssid	aw1_c_Whs10sfcQeub-wA5kxtjOQ	.zoom.us	/	Session	36	✓	✓				Medium
_zm_page_auth	aw1_c_5emyXdxkR9CCI6mGAphgAg	.zoom.us	/	Session	41	✓	✓	None			Medium
cred	D9D89EAC4B6183BA0E27EF4F158C7F5F	arden-ac-uk.zoom.us	/	Session	36	✓	✓				Medium
cf_clearance	crooJVGav0zrAN5tADaLaYgIEZCJdTJ0EMoCHdbsvgc-1773050751-1.2.1.1-F5thlrjXIFzIwgy0Ub0i2OLqC9NphYulP7rWzGHtX4OMg1G8EUDI1WnPag2H6wTpkrzZNi0bMN3_7K7VbBfMhnV4ClIY5ixZjNImQ79oQ7SvKiBqHV8dH1frrgQK2ieGbJ9n1_OtxlLgVeQAM9aPmSVRzGeRHZT35fJgAwfW58q9C1EdANnYSHn7u426f_bimR57PRVPi_6d_pzLNXXsAbmijs8947ba05jByMEs0z4	.zoom.us	/	2027-03-09T10:05:51.863Z	310	✓	✓	None	https://zoom.us		Medium
```

**Notice:** 
- Each line is ONE cookie
- Columns separated by TAB (not spaces)
- Lots of extra info we don't need

## The Pattern

Let me break down one line with colors/labels:

```
[NAME]          [VALUE]                                      [DOMAIN]    [PATH]  [EXPIRES]                [SIZE]  [...]
__cf_bm    	    .Xwx8a7juu6xJ4IhMFRkzjGqWOpLPxs...          .zoom.us    /       2026-03-09T10:50:38...   177     ✓ ✓ None Medium
```

**We only care about:**
- `__cf_bm` (Name - Column 1)
- `.Xwx8a7juu6xJ4IhMFRkzjGqWOpLPxs...` (Value - Column 2)

## What parse_cookies.py Does

```python
# For each line:
parts = line.split('\t')  # Split by TAB
name = parts[0]           # First column = name
value = parts[1]          # Second column = value
# Ignore parts[2], parts[3], parts[4]... (domain, path, expiry, etc.)

# Build JSON:
cookies[name] = value
```

## The Result (zoom_cookies.json)

```json
{
    "__cf_bm": ".Xwx8a7juu6xJ4IhMFRkzjGqWOpLPxs8ws94UZzOz8Y-1773051638-1.0.1.1-YMYCIqAEXnBBJ7NUqSFwsafsmV.CQCY6.fT9SuV8jwhefQ8LuYFAw5HtTZioknmPyD5mKOG.Rb7ZpyyzEcMSakhOjV7RF2bz23UHkTN3Tz0",
    "_zm_ssid": "aw1_c_Whs10sfcQeub-wA5kxtjOQ",
    "_zm_page_auth": "aw1_c_5emyXdxkR9CCI6mGAphgAg",
    "cred": "D9D89EAC4B6183BA0E27EF4F158C7F5F",
    "cf_clearance": "crooJVGav0zrAN5tADaLaYgIEZCJdTJ0EMoCHdbsvgc-1773050751-1.2.1.1-F5thlrjXIFzIwgy0Ub0i2OLqC9NphYulP7rWzGHtX4OMg1G8EUDI1WnPag2H6wTpkrzZNi0bMN3_7K7VbBfMhnV4ClIY5ixZjNImQ79oQ7SvKiBqHV8dH1frrgQK2ieGbJ9n1_OtxlLgVeQAM9aPmSVRzGeRHZT35fJgAwfW58q9C1EdANnYSHn7u426f_bimR57PRVPi_6d_pzLNXXsAbmijs8947ba05jByMEs0z4"
}
```

## Manual Conversion (Without the Script)

If you want to do it by hand:

### Step 1: Copy one cookie line
```
_zm_ssid	aw1_c_Whs10sfcQeub-wA5kxtjOQ	.zoom.us	/	Session	36	✓	✓		Medium
```

### Step 2: Extract name and value (first two columns)
- Name: `_zm_ssid`
- Value: `aw1_c_Whs10sfcQeub-wA5kxtjOQ`

### Step 3: Add to JSON
```json
{
    "_zm_ssid": "aw1_c_Whs10sfcQeub-wA5kxtjOQ"
}
```

### Step 4: Add more cookies
```json
{
    "_zm_ssid": "aw1_c_Whs10sfcQeub-wA5kxtjOQ",
    "cred": "D9D89EAC4B6183BA0E27EF4F158C7F5F"
}
```

**Notice:**
- Comma after each entry except the last
- Double quotes around both name and value
- All inside `{ }`

## The Easy Way

Just run:
```powershell
python parse_cookies.py
```

And paste the raw data when prompted. It does all the conversion automatically!

## How to Verify Your JSON is Valid

```powershell
# Test if the file is valid JSON
python -c "import json; json.load(open('zoom_cookies.json')); print('✓ Valid JSON')"
```

If it prints `✓ Valid JSON`, you're good to go!

If it shows an error, common issues:
- Missing comma between entries
- Single quotes instead of double quotes
- Extra comma after last entry
- Missing closing `}`
