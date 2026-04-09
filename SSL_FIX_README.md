# SSL Certificate Fix Guide

## Problem
Corporate proxy (Zscaler) intercepts HTTPS traffic using self-signed certificates, breaking SSL verification in development tools.

## Quick Navigation
From anywhere in PowerShell:
```powershell
cd "C:\Users\kulpaa\Python Projects\Video_downloader"
```

Or run directly:
```powershell
cd "C:\Users\kulpaa\Python Projects\Video_downloader"; .\Fix-SSLCertificates.ps1
```

**Pro tip:** Add this to your PowerShell profile for instant access:
```powershell
function video-dl { cd "C:\Users\kulpaa\Python Projects\Video_downloader" }
```
Then just type `video-dl` from anywhere!

## Quick Fix
Run as **Administrator**:
```powershell
.\Fix-SSLCertificates.ps1
```

This script:
1. ✓ Finds and exports your Zscaler/corporate certificate
2. ✓ Creates proper certificate bundle (corporate + system certs)
3. ✓ Sets environment variables for Python, Git, Node, Azure CLI, AWS CLI
4. ✓ Fixes Azure CLI's internal certificate store
5. ✓ Tests configuration
6. ✓ Shows detailed summary

## When to Re-run
- After Windows updates
- After Azure CLI updates
- When certificate expires/renews
- When SSL errors reappear
- After installing new dev tools

## What Gets Fixed

### ✓ Works Perfectly
- Python `requests` library
- Python `pip` package installation
- Python `httpx` (OpenAI SDK, etc.)
- Git operations
- Azure CLI (after updates, may need re-run)
- cURL commands
- Node.js with proper packages
- AWS CLI

### ⚠ Partial Fix
- Rust `reqwest` library - respects env vars partially
- Some npm packages - may need `--strict-ssl=false`
- Docker operations - may need daemon config

### ✗ Still Requires Workarounds
- `faster-whisper` model downloads - use download scripts
- Some Rust binaries - use Docker or Python alternatives

## Certificate Bundle Location
`C:\Users\<YourName>\corporate-ca-bundle.crt`

## Environment Variables Set
```
REQUESTS_CA_BUNDLE=C:\Users\<You>\corporate-ca-bundle.crt
SSL_CERT_FILE=C:\Users\<You>\corporate-ca-bundle.crt
CURL_CA_BUNDLE=C:\Users\<You>\corporate-ca-bundle.crt
GIT_SSL_CAINFO=C:\Users\<You>\corporate-ca-bundle.crt
NODE_EXTRA_CA_CERTS=C:\Users\<You>\corporate-ca-bundle.crt
AWS_CA_BUNDLE=C:\Users\<You>\corporate-ca-bundle.crt
```

## Verification
After running the script, test:
```powershell
# Python
python -c "import requests; print(requests.get('https://google.com').status_code)"

# Git  
git ls-remote https://github.com/git/git.git HEAD

# Azure CLI
az login
```

## Troubleshooting

### Still getting SSL errors?
1. Close ALL terminals and reopen (env vars need refresh)
2. Check certificate expiry: `Get-ChildItem Cert:\LocalMachine\Root\ | Where-Object Subject -match zscaler`
3. Re-run script
4. Check if corporate cert changed (IT update)

### Azure CLI still failing?
Azure CLI updates reset the cacert.pem file. Just re-run the script.

### Faster-whisper still broken?
Rust's reqwest doesn't fully respect certificate env vars. Use:
- Base model (already downloaded and working)
- Azure Speech Service (recommended)
- Manual download script (included in repo)

## For Future: Azure Speech Service
Instead of local transcription with SSL issues, use Azure:
```powershell
# Install Azure Speech SDK
pip install azure-cognitiveservices-speech

# Configure (after running Fix-SSLCertificates.ps1)
az login
az account set --subscription <your-sub>
```

Benefits:
- ✓ No local model downloads
- ✓ SOTA transcription quality
- ✓ No SSL workarounds needed (fixed by this script)
- ✓ Batch processing
- ✓ Speaker diarization available
