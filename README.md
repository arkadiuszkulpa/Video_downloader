# Video Downloader & Transcription Pipeline

Python toolkit for downloading videos, extracting audio, generating transcripts, and analyzing content using AI.

## Features

- Download videos with resume support
- Extract audio from video files
- Transcribe audio using Whisper AI
- Analyze transcripts with Claude AI

## Requirements

- Python 3.x
- FFmpeg
- Dependencies: `requests`, `faster-whisper`, `torch`, `boto3`

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
```bash
# Transcribe specific file
python transcribe.py "dump/your_audio_file.mp3"

# Or transcribe default audio.mp3
python transcribe.py
```

### 4. Analyze Transcript
```bash
# Analyze specific transcript file
python analysis.py "dump/your_transcript_file.txt"

# Analyze default transcript.txt
python analysis.py

# Override AWS settings
python analysis.py "dump/transcript.txt" --secret-name "my-secret" --region "us-east-1"
```

Optional arguments:
- `--secret-name` - AWS Secrets Manager secret name (default: env `AWS_SECRET_NAME` or `anthropic/default`)
- `--region` - AWS region (default: env `AWS_REGION` or `eu-west-2`)

**Features:**
- Overlapping chunks (500 char) to preserve context
- Comprehensive summaries covering ALL topics (not just highlights)
- Topic-organized output
- Saves to `_analysis.txt` file

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
