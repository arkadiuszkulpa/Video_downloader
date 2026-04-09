# SSL Certificate Bypass - Complete Implementation

## Overview

SSL certificate verification has been disabled across all network operations to support corporate proxy environments with self-signed certificates.

## Components with SSL Bypass

### 1. Video/Audio Downloader
**File:** [core/downloader.py](core/downloader.py)

**Implementation:**
```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# All requests include verify=False
response = requests.get(url, verify=False, allow_redirects=True)
```

**Affects:**
- Video downloads from public URLs
- Video downloads from authenticated URLs (Zoom, etc.)
- Resume functionality

---

### 2. Whisper Model Downloads
**File:** [core/transcriber.py](core/transcriber.py), [transcribe.py](transcribe.py)

**Implementation:**
```python
# Environment variables set BEFORE importing faster-whisper
os.environ['SSL_CERT_FILE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

from faster_whisper import WhisperModel
```

**Manual downloader:** [download_whisper_model.py](download_whisper_model.py)
```python
import urllib3
urllib3.disable_warnings()

# Uses Python requests with verify=False
response = requests.get(url, verify=False)
```

**Affects:**
- Whisper model downloads from HuggingFace
- Transcription initialization

**Note:** Environment variables must be set in shell before Python starts

---

### 3. Transcript Analysis
**File:** [core/analyzer.py](core/analyzer.py), [analysis.py](analysis.py)

**Implementation:**
```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# All API requests include verify=False
response = requests.post(endpoint, json=payload, headers=headers, verify=False)
```

**Affects:**
- Anthropic API calls
- Databricks API calls
- OpenAI API calls
- Any custom API endpoint

---

## Why This Is Needed

### The Problem
Corporate networks often use:
- SSL/TLS inspection proxies
- Self-signed certificates
- Custom certificate authorities (CA)

These certificates are not in Python's default trust store, causing:
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: 
unable to get local issuer certificate
```

### The Solution
Disable SSL verification with `verify=False` in requests:
- Allows connections through corporate proxies
- Bypasses certificate validation
- Enables functionality without IT certificate configuration

### Security Implications
⚠️ **Important:**
- SSL verification is disabled for **all** network requests
- Traffic can potentially be intercepted by proxies
- Assumes corporate network is trusted
- Not recommended for production deployments handling sensitive data

**For production use:**
- Configure proper CA certificates
- Use environment variables: `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`
- Install corporate root CA in system trust store

---

## Complete SSL Bypass Checklist

| Component | File | Status | Method |
|-----------|------|--------|--------|
| Downloads | core/downloader.py | ✅ | `verify=False` in requests |
| Whisper Download | download_whisper_model.py | ✅ | `verify=False` in requests |
| Whisper Init | transcribe.py, core/transcriber.py | ✅ | Environment variables |
| Analysis API | core/analyzer.py, analysis.py | ✅ | `verify=False` in requests |

---

## Testing SSL Bypass

### Test 1: Download
```powershell
python main.py "https://example.com/video.mp4" --no-auth
# Should succeed without SSL errors
```

### Test 2: Transcription
```powershell
# Download model
python download_whisper_model.py base

# Transcribe with env vars
$env:SSL_CERT_FILE=""; python transcribe.py "video.mp4"
# Should load model without SSL errors
```

### Test 3: Analysis
```powershell
python analysis.py "transcript.txt" \
    --api-key "dapi..." \
    --endpoint "https://databricks.com/..." \
    --model "llama-3-70b"
# Should connect to API without SSL errors
```

---

## When SSL Bypass Is NOT Enough

Some components use libraries that manage SSL independently:

### faster-whisper (Rust reqwest)
- **Problem:** Rust HTTP client doesn't respect Python's `verify=False`
- **Solution:** Environment variables set before Python starts
- **Files:** [WHISPER_SSL_FIX.md](WHISPER_SSL_FIX.md), [TRANSCRIBE_QUICKSTART.md](TRANSCRIBE_QUICKSTART.md)

### Workaround Script
For Whisper: [download_whisper_model.py](download_whisper_model.py) uses Python requests to pre-download models

---

## Configuration Notes

### No Configuration Needed ✅
SSL bypass is **automatic** for:
- ✅ Downloads (all sources)
- ✅ Analysis (all providers)

### Manual Configuration Required 🔧
For transcription, set environment variables:
```powershell
# PowerShell
$env:SSL_CERT_FILE=""
$env:REQUESTS_CA_BUNDLE=""
$env:CURL_CA_BUNDLE=""

# Then run Python
python transcribe.py "file.mp4"
```

Or use wrapper scripts:
```powershell
.\transcribe.ps1 "file.mp4"
```

---

## Alternative: Configure Proper Certificates

If SSL bypass is not acceptable, configure certificates properly:

### Option 1: System-wide CA Installation
1. Export corporate root CA certificate
2. Install in Windows Certificate Store
3. Python will use system certificates

### Option 2: Environment Variable
```powershell
# Point to CA bundle file
$env:REQUESTS_CA_BUNDLE="C:\path\to\corporate-ca-bundle.crt"
$env:SSL_CERT_FILE="C:\path\to\corporate-ca-bundle.crt"
```

### Option 3: Modify Code
Remove `verify=False` and configure certifi:
```python
import certifi
certifi.where()  # Find cert location
# Add corporate CA to this file
```

---

## Summary

**Current approach:** SSL verification disabled across all components for maximum corporate network compatibility.

**Trade-off:** Convenience vs. security - acceptable for internal tools in trusted networks.

**Alternative:** Proper certificate configuration requires IT support but provides full SSL/TLS security.

You'll likely see warnings like:
```
InsecureRequestWarning: Unverified HTTPS request is being made
```

These are **suppressed** with `urllib3.disable_warnings()` but indicate SSL verification is bypassed.
