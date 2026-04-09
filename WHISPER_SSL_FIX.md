# Whisper Transcription SSL Fix Guide

## Problem
Whisper model downloads fail with SSL certificate errors on corporate networks:
```
[ERROR] Transcription error: Xet Runtime Error: Task Panic: "JoinError::Panic(Id(14), 
\"failed to create reqwest client: reqwest::Error { kind: Builder, source: 
\\\"zero valid certificates found in native root store\\\" }\", ...)"
```

## Root Cause
- `faster-whisper` uses a Rust HTTP client (reqwest) to download models from HuggingFace
- This Rust client requires valid SSL certificates in the Windows native certificate store
- Corporate proxies with self-signed certificates break SSL validation
- Environment variables must be set **BEFORE** Python starts to affect the Rust client

## ✅ WORKING SOLUTION

### Required: Set Environment Variables Before Running Python

The Rust reqwest client reads these environment variables at startup. You **MUST** set them in the same command or use a wrapper script.

**Working Method (PowerShell - one-liner):**
```powershell
$env:SSL_CERT_FILE=""; $env:REQUESTS_CA_BUNDLE=""; $env:CURL_CA_BUNDLE=""; python transcribe.py "path\to\video.mp4"
```

**Or use the wrapper script:**
```powershell
.\transcribe.ps1 "path\to\video.mp4"
```

### Step 1: Pre-Download Model (One-Time Setup)
Before first use, download the Whisper model with SSL bypass enabled:

### Step 1: Pre-Download Model (One-Time Setup)
Before first use, download the Whisper model with SSL bypass enabled:

```powershell
# Download the 'base' model (~145 MB) - RECOMMENDED for most uses
python download_whisper_model.py base

# Or choose a different model:
# python download_whisper_model.py tiny    # ~75 MB - fastest, lowest accuracy
# python download_whisper_model.py small   # ~470 MB - better accuracy
# python download_whisper_model.py medium  # ~1.5 GB - high accuracy
```

Expected output:
```
======================================================================
Whisper Model Downloader (SSL Bypass Mode)
======================================================================
Model: base
Size: ~145 MB

Download location: C:\Users\[username]\.cache\huggingface\hub\...

Downloading model files...
Downloading config.json...
✓ config.json
Downloading model.bin...
  model.bin: 100.0%
✓ model.bin
Downloading tokenizer.json...
✓ tokenizer.json
Downloading vocabulary.txt...
✓ vocabulary.txt

======================================================================
✓ Model download complete!
======================================================================

The model is now cached and ready to use.
```

**Important:** After downloading, copy files to the commit-specific directory:
```powershell
# Find the commit hash directory (will be a long hex string)
$commitHash = (Get-ChildItem "C:\Users\$env:USERNAME\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots" -Directory | Where-Object { $_.Name -ne "main" }).Name

# Copy files from main to the commit directory
Copy-Item "C:\Users\$env:USERNAME\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\main\*" -Destination "C:\Users\$env:USERNAME\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\$commitHash\" -Force

Write-Host "✓ Model files copied to correct location"
```

### Step 2: Run Transcription with SSL Bypass

Once the model is downloaded and in the correct location, run transcription:

**Method 1: PowerShell One-Liner (Recommended)**
```powershell
$env:SSL_CERT_FILE=""; $env:REQUESTS_CA_BUNDLE=""; $env:CURL_CA_BUNDLE=""; python transcribe.py "path\to\video.mp4"
```

**Method 2: Use Wrapper Script**
```powershell
.\transcribe.ps1 "path\to\video.mp4"
```

**Method 3: Set Variables for Session**
```powershell
# Set once for the entire PowerShell session
$env:SSL_CERT_FILE=""
$env:REQUESTS_CA_BUNDLE=""
$env:CURL_CA_BUNDLE=""

# Then run as many transcriptions as needed
python transcribe.py "video1.mp4"
python transcribe.py "video2.mp4"
```

## Expected Behavior

### ✅ Successful Transcription
```
CUDA available: False
[2026-03-09 11:18:20.089] [ctranslate2] [thread 26788] [warning] The compute type inferred from the saved model is float16, but the target device or backend do not support efficient float16 computation. The model weights have been automatically converted to use the float32 compute type instead.
Transcribing: dump\impactWorkshop1\GMT20260212-090807_Recording_1920x1200_20260309_104511.mp4
[Processing segments - this may take several minutes...]
Transcription saved to dump\impactWorkshop1\GMT20260212-090807_Recording_1920x1200_20260309_104511_transcript.txt
```

**Note:** The float16→float32 warning is normal on CPU and can be ignored.

### ❌ Failed - SSL Error (Environment Variables Not Set)
```
thread 'hf-xet-0' panicked at ...:
failed to create reqwest client: reqwest::Error { kind: Builder, source: "zero valid certificates found in native root store" }
```

**Solution:** You forgot to set environment variables. Use Method 1 or 2 above.

### ❌ Failed - Model Files Not Found
```
RuntimeError: Unable to open file 'model.bin' in model 'C:\Users\...\faster-whisper-base\snapshots\[hash]'
```

**Solution:** Run the copy command from Step 1 to move files to the correct snapshot directory.

### ❌ Failed - Invalid Data Error
```
av.error.InvalidDataError: [Errno 1094995529] Invalid data found when processing input
```

**Solution:** The video file is corrupted or incomplete. Try a different file.

## Troubleshooting

### Problem: Still getting SSL errors
**Cause:** Environment variables weren't set before Python started

**Solution:**
```powershell
# ✅ CORRECT - Set env vars BEFORE python command
$env:SSL_CERT_FILE=""; $env:REQUESTS_CA_BUNDLE=""; $env:CURL_CA_BUNDLE=""; python transcribe.py "file.mp4"

# ❌ WRONG - Setting inside Python code doesn't help (Rust client already initialized)
# python transcribe.py "file.mp4"  # This will fail even if transcribe.py sets os.environ
```

### Problem: Model not found after download
**Cause:** HuggingFace downloads to "main" folder but faster-whisper looks in commit-specific folder

**Solution:**
```powershell
# List snapshot directories to find the commit hash
Get-ChildItem "C:\Users\$env:USERNAME\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots"

# You'll see: main (where we downloaded) and [long-hash] (where faster-whisper looks)
# Copy files from main to the hash directory:
$hash = (Get-ChildItem "C:\Users\$env:USERNAME\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots" -Directory | Where-Object { $_.Name -ne "main" }).Name
Copy-Item "C:\Users\$env:USERNAME\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\main\*" -Destination "C:\Users\$env:USERNAME\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\$hash\" -Force
```

### Problem: Missing module 'httpx'
**Cause:** HuggingFace Hub requires httpx package

**Solution:**
```powershell
pip install httpx
```

### Problem: Transcription is very slow
**Possible solutions:**
- Use a smaller model: `tiny` (fastest) or `base` instead of `large`
- Use GPU if available: Change `device="cpu"` to `device="cuda"` in transcribe.py
- Check CUDA availability:
  ```powershell
  python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
  ```

### Problem: Video file gives "Invalid data" error
**Cause:** The video file may be corrupted, incomplete, or in an unsupported format

**Solution:**
- Verify the file plays in a media player
- Check file size - very small files may be incomplete downloads
- Try converting to a standard format (MP4, MP3, WAV) using FFmpeg
- Test with a different known-good video file

## Files Created/Modified

### Scripts
- **[download_whisper_model.py](download_whisper_model.py)** - Manual model downloader with SSL bypass (uses Python requests, not Rust)
- **[transcribe.ps1](transcribe.ps1)** - PowerShell wrapper that sets environment variables before running transcribe.py
- **[transcribe.bat](transcribe.bat)** - Batch file wrapper (alternative to .ps1)

### Source Code
- **[core/transcriber.py](core/transcriber.py)** - Transcription logic (environment variables added, but must be set before Python starts)
- **[transcribe.py](transcribe.py)** - Standalone transcription script

### Documentation
- **[WHISPER_SSL_FIX.md](WHISPER_SSL_FIX.md)** - This guide

## Quick Reference

### ✅ DO THIS - Working Commands

```powershell
# First time setup (download model)
python download_whisper_model.py base

# Copy model files to correct location
$hash = (Get-ChildItem "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots" -Directory | Where-Object { $_.Name -ne "main" }).Name
Copy-Item "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\main\*" -Destination "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\$hash\" -Force

# Every time: Transcribe with SSL bypass
$env:SSL_CERT_FILE=""; $env:REQUESTS_CA_BUNDLE=""; $env:CURL_CA_BUNDLE=""; python transcribe.py "path\to\video.mp4"
```

### ❌ DON'T DO THIS - Won't Work

```powershell
# ❌ Running without environment variables - will fail with SSL error
python transcribe.py "video.mp4"

# ❌ Setting env vars after Python starts - too late, Rust client already initialized
# (code inside transcribe.py that does os.environ['SSL_CERT_FILE'] = '' won't help)
```

## Model Sizes & Accuracy Trade-offs

| Model | Size | Speed | Accuracy | Recommendation |
|-------|------|-------|----------|----------------|
| tiny | 75 MB | ⚡⚡⚡⚡ | ⭐⭐ | Quick previews only |
| **base** | **145 MB** | **⚡⚡⚡** | **⭐⭐⭐** | **Best for most uses** ✅ |
| small | 470 MB | ⚡⚡ | ⭐⭐⭐⭐ | Better accuracy needed |
| medium | 1.5 GB | ⚡ | ⭐⭐⭐⭐⭐ | Professional transcription |
| large | 3 GB | 🐌 | ⭐⭐⭐⭐⭐ | Maximum accuracy |

## Complete Example Workflow

```powershell
# 1. Activate your environment
conda activate fabric

# 2. Install required dependency (first time only)
pip install httpx

# 3. Download model (first time only)
python download_whisper_model.py base

# 4. Copy model files to correct location (first time only)
$hash = (Get-ChildItem "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots" -Directory | Where-Object { $_.Name -ne "main" }).Name
Copy-Item "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\main\*" -Destination "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\$hash\" -Force

# 5. Transcribe your video (every time)
$env:SSL_CERT_FILE=""; $env:REQUESTS_CA_BUNDLE=""; $env:CURL_CA_BUNDLE=""; python transcribe.py "dump\impactWorkshop1\video.mp4"

# 6. Check the output
Get-Content "dump\impactWorkshop1\video_transcript.txt"
```

## Success Indicators ✅

You know it's working when you see:
1. ✅ **No SSL panic messages** in the output
2. ✅ `CUDA available: False` (or True if you have GPU)
3. ✅ `[ctranslate2]` warning about float16→float32 (this is normal and safe to ignore)
4. ✅ `Transcribing: [your file path]`
5. ✅ Eventually: `Transcription saved to [output path]`

## Why Environment Variables Must Be Set Before Python

The `faster-whisper` library uses a Rust crate called `reqwest` for HTTP downloads. This Rust code:
- Initializes its SSL certificate store when the module loads
- Reads environment variables **only during initialization**
- Cannot be reconfigured after initialization

Therefore, setting `os.environ['SSL_CERT_FILE'] = ''` inside Python code (after imports) has no effect on the Rust client that was already initialized with the original environment.

**Solution:** Always set environment variables in PowerShell/CMD **before** running `python`.
