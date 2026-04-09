"""
Download faster-whisper-large-v3 model with SSL bypass.

This script manually downloads the model files using Python requests
to bypass SSL certificate verification issues.
"""

import os
import requests
import urllib3
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Model details
MODEL_NAME = "faster-whisper-large-v3"
REPO_ID = "Systran/faster-whisper-large-v3"
REVISION = "main"

# Files to download
FILES = [
    "config.json",
    "model.bin",
    "tokenizer.json", 
    "vocabulary.json",
    "preprocessor_config.json"
]

# Cache directory
CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"
MODEL_DIR = CACHE_DIR / f"models--{REPO_ID.replace('/', '--')}"
SNAPSHOT_DIR = MODEL_DIR / "snapshots" / REVISION

def download_file(filename):
    """Download a single model file."""
    url = f"https://huggingface.co/{REPO_ID}/resolve/{REVISION}/{filename}"
    output_path = SNAPSHOT_DIR / filename
    
    print(f"\n{'='*70}")
    print(f"Downloading: {filename}")
    print(f"From: {url}")
    print(f"To: {output_path}")
    print(f"{'='*70}")
    
    try:
        # Stream download to handle large files
        response = requests.get(url, verify=False, stream=True, timeout=300)
        response.raise_for_status()
        
        # Get file size
        total_size = int(response.headers.get('content-length', 0))
        total_mb = total_size / (1024 * 1024)
        
        print(f"File size: {total_mb:.2f} MB")
        
        # Download with progress
        downloaded = 0
        chunk_size = 8192
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress update every 10MB
                    if downloaded % (10 * 1024 * 1024) < chunk_size:
                        progress = (downloaded / total_size * 100) if total_size > 0 else 0
                        downloaded_mb = downloaded / (1024 * 1024)
                        print(f"Progress: {progress:.1f}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)")
        
        final_size = output_path.stat().st_size
        final_mb = final_size / (1024 * 1024)
        print(f"✓ Downloaded successfully: {final_mb:.2f} MB")
        return True
        
    except Exception as e:
        print(f"✗ Error downloading {filename}: {e}")
        return False

def main():
    print("="*70)
    print("FASTER-WHISPER LARGE-V3 MODEL DOWNLOADER")
    print("="*70)
    print(f"\nModel: {MODEL_NAME}")
    print(f"Repository: {REPO_ID}")
    print(f"Cache directory: {SNAPSHOT_DIR}")
    print(f"\nThis will download ~3 GB of model files.")
    print("SSL verification is disabled to work with corporate proxies.")
    
    # Create directories
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n✓ Created cache directory")
    
    # Download each file
    print(f"\n{'='*70}")
    print("STARTING DOWNLOADS")
    print(f"{'='*70}")
    
    success_count = 0
    failed_files = []
    
    for filename in FILES:
        print(f"\n[{FILES.index(filename) + 1}/{len(FILES)}] Processing {filename}...")
        
        if download_file(filename):
            success_count += 1
        else:
            failed_files.append(filename)
    
    # Summary
    print(f"\n{'='*70}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successfully downloaded: {success_count}/{len(FILES)} files")
    
    if failed_files:
        print(f"✗ Failed files: {', '.join(failed_files)}")
        print("\nYou can re-run this script to retry failed downloads.")
    else:
        print("\n✓ All files downloaded successfully!")
        print("\nThe large-v3 model is now ready to use in the GUI.")
        print("Select 'large-v3' from the Model dropdown in the Transcribe tab.")
    
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
