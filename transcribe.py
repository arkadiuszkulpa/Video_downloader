from faster_whisper import WhisperModel
import torch
import os
import sys

# Ensure dump folder exists
os.makedirs("dump", exist_ok=True)

print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("CUDA device name:", torch.cuda.get_device_name(0))

# Use "cuda" for GPU, "cpu" for CPU
model = WhisperModel("base", device="cpu")  # change to "cpu" if no GPU (cuda)

# Accept audio file path as argument, or use default
if len(sys.argv) > 1:
    audio_input = sys.argv[1]
else:
    audio_input = os.path.join("dump", "audio.mp3")

# Generate output transcript filename based on input audio filename
audio_basename = os.path.splitext(os.path.basename(audio_input))[0]
transcript_output = os.path.join("dump", f"{audio_basename}_transcript.txt")

print(f"Transcribing: {audio_input}")
segments, info = model.transcribe(audio_input)
with open(transcript_output, "w", encoding="utf-8") as f:
    for segment in segments:
        f.write(segment.text + "\n")
print(f"Transcription saved to {transcript_output}")
