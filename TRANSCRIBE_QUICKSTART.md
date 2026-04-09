# Whisper Transcription - Quick Start

## First Time Setup (Do Once)

```powershell
# 1. Activate environment
conda activate fabric

# 2. Install dependency
pip install httpx

# 3. Download Whisper model
python download_whisper_model.py base

# 4. Copy model to correct location
$hash = (Get-ChildItem "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots" -Directory | Where-Object { $_.Name -ne "main" }).Name
Copy-Item "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\main\*" -Destination "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-base\snapshots\$hash\" -Force
```

## Every Time You Transcribe

```powershell
# Set SSL bypass vars and run transcription (one command)
$env:SSL_CERT_FILE=""; $env:REQUESTS_CA_BUNDLE=""; $env:CURL_CA_BUNDLE=""; python transcribe.py "path\to\video.mp4"
```

**Or use the wrapper:**
```powershell
.\transcribe.ps1 "path\to\video.mp4"
```

## Output

Transcript saved to: `path\to\video_transcript.txt`

## Troubleshooting

**SSL Error?** → You forgot to set environment variables. Use the command above.

**Model not found?** → Run Step 4 from First Time Setup.

**httpx missing?** → Run `pip install httpx`

---

See [WHISPER_SSL_FIX.md](WHISPER_SSL_FIX.md) for detailed documentation.
