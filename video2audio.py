import subprocess
import os

# Ensure dump folder exists
os.makedirs("dump", exist_ok=True)

input_video = os.path.join("dump", "video.mp4")
output_audio = os.path.join("dump", "audio.mp3")

print("Extracting audio from video...")
subprocess.run([
    "ffmpeg", "-y", "-i", input_video, "-vn", "-acodec", "libmp3lame", output_audio
])
print(f"Audio saved as {output_audio}")
