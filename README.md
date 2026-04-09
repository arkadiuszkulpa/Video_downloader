# Video Downloader & Transcription Pipeline

Python toolkit for downloading videos, extracting audio, generating transcripts, and analyzing content using AI.

## Features

- Download videos with resume support (public URLs and authenticated intranet sites)
- Extract audio from video files
- Transcribe audio using Whisper AI
- Analyze transcripts with Claude AI

## Requirements

- Python 3.x
- FFmpeg
- Dependencies: `requests`, `faster-whisper`, `torch`
- Optional: `boto3` (AWS Secrets Manager only)

## 📖 Special Guides

### Downloads
- **[ZOOM_DOWNLOAD_GUIDE.md](ZOOM_DOWNLOAD_GUIDE.md)** - Download from Zoom with cookie authentication
- **[COOKIE_MANAGEMENT.md](COOKIE_MANAGEMENT.md)** - Managing and updating authentication cookies
- **[COOKIE_FORMAT_GUIDE.md](COOKIE_FORMAT_GUIDE.md)** - Understanding cookie formats from DevTools

### Transcription
- **[TRANSCRIBE_QUICKSTART.md](TRANSCRIBE_QUICKSTART.md)** - Quick start guide for Whisper transcription ⭐
- **[WHISPER_SSL_FIX.md](WHISPER_SSL_FIX.md)** - Fix SSL certificate errors on corporate networks

### Analysis
- **[DATABRICKS_ANALYSIS_GUIDE.md](DATABRICKS_ANALYSIS_GUIDE.md)** - Using Databricks served models for analysis ⭐

### Technical
- **[SSL_BYPASS_OVERVIEW.md](SSL_BYPASS_OVERVIEW.md)** - Complete SSL bypass implementation details

## Usage

### 1. Download Video or Audio
```bash
# For public URLs (recommended for most cases)
python main.py "URL" --no-auth

# For authenticated URLs (uses default headers/cookies)
python main.py "URL"
```

Optional arguments:
- `--output-dir DIR` - Output directory (default: `dump/`)
- `--headers-file FILE` - Custom headers JSON file
- `--cookies-file FILE` - Custom cookies JSON file
- `--no-auth` - Skip authentication (for public URLs)

**Features:**
- Auto-detects audio vs video files
- Extracts original filename from URL
- Adds timestamp to prevent overwriting
- Supports resume for interrupted downloads

### 2. Extract Audio (Video files only)
```bash
python video2audio.py
```

### 3. Transcribe Audio

**Quick Start:**
```powershell
# First time: Download Whisper model
python download_whisper_model.py base

# Transcribe video/audio (SSL bypass for corporate networks)
$env:SSL_CERT_FILE=""; $env:REQUESTS_CA_BUNDLE=""; $env:CURL_CA_BUNDLE=""; python transcribe.py "dump/video.mp4"

# Or use wrapper script
.\transcribe.ps1 "dump/video.mp4"
```

**Note:** On corporate networks with SSL proxies, you must set environment variables before running Python. See [TRANSCRIBE_QUICKSTART.md](TRANSCRIBE_QUICKSTART.md) for details.

**Models:**
- `tiny` (75 MB) - Fast, basic accuracy
- `base` (145 MB) - Recommended for most uses ⭐
- `small` (470 MB) - Better accuracy
- `medium` (1.5 GB) - Professional quality

### 4. Analyze Transcript

**Using Anthropic (Claude):**
```bash
# AWS Secrets Manager
python analysis.py "dump/transcript.txt" --secret-name "anthropic/other" --region "eu-west-2"

# Direct API key
python analysis.py "dump/transcript.txt" --api-key "sk-ant-..."
```

**Using Databricks Served Models:**
```bash
python analysis.py "dump/transcript.txt" \
    --api-key "dapi1234567890..." \
    --endpoint "https://[workspace].databricks.com/serving-endpoints/[model]/invocations" \
    --model "databricks-meta-llama-3-70b-instruct" \
    --provider databricks
```

**Using OpenAI:**
```bash
python analysis.py "dump/transcript.txt" \
    --api-key "sk-..." \
    --endpoint "https://api.openai.com/v1/chat/completions" \
    --model "gpt-4" \
    --provider openai
```

Optional arguments:
- `--api-key` - Direct API key (any provider)
- `--secret-name` - AWS Secrets Manager secret name (Anthropic only)
- `--region` - AWS region (default: `eu-west-2`)
- `--endpoint` - API endpoint URL (auto-detects provider)
- `--model` - Model name
- `--provider` - API provider (`anthropic`, `databricks`, `openai`, or `auto`)

**Features:**
- Multiple API provider support (Anthropic, Databricks, OpenAI)
- Overlapping chunks (200 char) to preserve context
- Concise summaries extracting key points and main ideas
- Topic-organized output
- Saves to `_analysis.txt` file

See [DATABRICKS_ANALYSIS_GUIDE.md](DATABRICKS_ANALYSIS_GUIDE.md) for detailed Databricks setup.

## Output

All files are saved to the `dump/` folder:
- `video.mp4` / `video_fixed.mp4` - Downloaded video
- `audio.mp3` - Extracted audio
- `transcript.txt` - Transcription

## Notes

- The `dump/` folder is automatically created and git-ignored
- Analysis requires AWS credentials for Anthropic API key retrieval

## Future Enhancements

### Modular Downloader Architecture
- [ ] Refactor downloader logic into modular components
- [ ] **Direct URL Downloader** - Current implementation for direct `.mp4` links (e.g., instytutkryptografii.pl)
- [ ] **YouTube Downloader** - Integrate `yt-dlp` library for YouTube video downloads
- [ ] **Embedded Video Downloader** - Extract and download videos embedded in third-party platforms
- [ ] Auto-detect video source type and route to appropriate downloader module
