"""
Manual Whisper Model Downloader with SSL Bypass

This script downloads Whisper models using Python requests with SSL verification
disabled, working around corporate proxy certificate issues.

Usage:
    python download_whisper_model.py [model_size]
    
    Available models: tiny, base, small, medium, large, large-v2, large-v3
    Default: base
"""

import os
import sys
import requests
import urllib3
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AVAILABLE_MODELS = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']

MODEL_SIZES = {
    'tiny': '75 MB',
    'base': '145 MB',
    'small': '470 MB',
    'medium': '1.5 GB',
    'large': '3 GB',
    'large-v2': '3 GB',
    'large-v3': '3 GB',
}

def download_file(url, destination, desc="Downloading"):
    """Download a file with progress indication."""
    response = requests.get(url, stream=True, verify=False)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"\r{desc}: {percent:.1f}%", end='', flush=True)
    
    print()  # New line after progress

def download_whisper_model(model_size='base'):
    """
    Download Whisper model files from Hugging Face.
    
    Args:
        model_size (str): Model size to download
    """
    if model_size not in AVAILABLE_MODELS:
        print(f"ERROR: Invalid model size '{model_size}'")
        print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
        return False
    
    print(f"=" * 70)
    print(f"Whisper Model Downloader (SSL Bypass Mode)")
    print(f"=" * 70)
    print(f"Model: {model_size}")
    print(f"Size: ~{MODEL_SIZES[model_size]}")
    print()
    
    # Determine cache directory (same as faster-whisper uses)
    try:
        from huggingface_hub import constants
        cache_dir = Path(constants.HF_HUB_CACHE)
    except ImportError:
        # Fallback to default location
        cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
    
    # Model repository and version
    repo_id = f"Systran/faster-whisper-{model_size}"
    model_dir = cache_dir / f"models--Systran--faster-whisper-{model_size}"
    
    print(f"Download location: {model_dir}")
    print()
    
    # Create directory structure
    snapshots_dir = model_dir / "snapshots"
    os.makedirs(snapshots_dir, exist_ok=True)
    
    # Files to download (key model files)
    base_url = f"https://huggingface.co/{repo_id}/resolve/main"
    
    files_to_download = [
        "config.json",
        "model.bin",
        "tokenizer.json",
        "vocabulary.txt"
    ]
    
    # Try to get the latest snapshot hash from refs
    refs_dir = model_dir / "refs"
    os.makedirs(refs_dir, exist_ok=True)
    
    # Use 'main' as snapshot ID
    snapshot_id = "main"
    snapshot_path = snapshots_dir / snapshot_id
    os.makedirs(snapshot_path, exist_ok=True)
    
    # Save snapshot reference
    with open(refs_dir / "main", "w") as f:
        f.write(snapshot_id)
    
    print("Downloading model files...")
    print()
    
    success = True
    for filename in files_to_download:
        file_url = f"{base_url}/{filename}"
        destination = snapshot_path / filename
        
        # Skip if already exists
        if destination.exists():
            print(f"✓ {filename} (already exists)")
            continue
        
        try:
            print(f"Downloading {filename}...")
            download_file(file_url, destination, f"  {filename}")
            print(f"✓ {filename}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠ {filename} (not found - may be optional)")
            else:
                print(f"✗ {filename} (error: {e})")
                success = False
        except Exception as e:
            print(f"✗ {filename} (error: {e})")
            success = False
    
    print()
    if success:
        print("=" * 70)
        print("✓ Model download complete!")
        print("=" * 70)
        print()
        print("The model is now cached and ready to use.")
        print("You can run transcription without downloading again.")
        return True
    else:
        print("=" * 70)
        print("⚠ Model download completed with some errors")
        print("=" * 70)
        print()
        print("Some files may not have downloaded successfully.")
        print("The model may still work if core files were downloaded.")
        return False

def main():
    """Main entry point."""
    # Get model size from command line
    if len(sys.argv) > 1:
        model_size = sys.argv[1].lower()
    else:
        model_size = 'base'
        print(f"No model specified, using default: {model_size}")
        print(f"Usage: python {os.path.basename(__file__)} [model_size]")
        print()
    
    try:
        success = download_whisper_model(model_size)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
