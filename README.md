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

### 1. Download Video
```bash
python main.py "VIDEO_URL"
```

Optional arguments:
- `--output-dir DIR` - Output directory (default: `dump/`)
- `--headers-file FILE` - Custom headers JSON file
- `--cookies-file FILE` - Custom cookies JSON file

### 2. Extract Audio
```bash
python video2audio.py
```

### 3. Transcribe Audio
```bash
python transcribe.py
```

### 4. Analyze Transcript
```bash
python analysis.py
```

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
