"""Azure Speech Service transcription with progress callbacks."""

import os
import sys
import json
import time
from pathlib import Path

# Add local lib directory to path FIRST to avoid namespace package conflicts
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if os.path.exists(lib_path) and lib_path not in sys.path:
    sys.path.insert(0, lib_path)

import azure.cognitiveservices.speech as speechsdk


class AzureSpeechTranscriber:
    """
    Audio transcription using Azure Speech Service.
    
    Features:
    - State-of-the-art transcription quality
    - Automatic language detection
    - Speaker diarization (optional)
    - Progress reporting
    - No local model storage needed
    """
    
    def __init__(self, progress_callback=None):
        """
        Initialize Azure Speech transcriber.
        
        Args:
            progress_callback (ProgressCallback, optional): Callback for progress updates
        """
        self.progress_callback = progress_callback
        self._speech_config = None
    
    def transcribe(self, audio_file, output_dir, 
                   speech_key=None, speech_region=None,
                   language='en-US', enable_diarization=False):
        """
        Transcribe audio file using Azure Speech Service.
        
        Args:
            audio_file (str): Path to audio/video file
            output_dir (str): Directory to save transcript
            speech_key (str): Azure Speech Service subscription key
            speech_region (str): Azure region (e.g., 'eastus', 'westeurope')
            language (str, optional): Language code. Default 'en-US'
            enable_diarization (bool, optional): Enable speaker identification
        
        Returns:
            tuple: (success, transcript_path, message)
        """
        try:
            self._log("Starting Azure Speech Service transcription...", "info")
            
            # Validate inputs
            if not os.path.exists(audio_file):
                error_msg = f"Audio file not found: {audio_file}"
                self._log(error_msg, "error")
                return False, "", error_msg
            
            if not speech_key or not speech_region:
                error_msg = "Azure Speech Service credentials required (key and region)"
                self._log(error_msg, "error")
                return False, "", error_msg
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output filename
            base_name = Path(audio_file).stem
            transcript_path = os.path.join(output_dir, f"{base_name}_transcript.txt")
            json_path = os.path.join(output_dir, f"{base_name}_transcript.json")
            
            # Configure Speech SDK
            self._log(f"Connecting to Azure Speech Service ({speech_region})...", "info")
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=speech_region
            )
            
            # Configure recognition settings
            speech_config.speech_recognition_language = language
            speech_config.request_word_level_timestamps()
            
            if enable_diarization:
                speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_EnableSpeakerDiarization,
                    "true"
                )
                self._log("Speaker diarization enabled", "info")
            
            # Create audio config
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            # Storage for results
            all_results = []
            full_transcript = []
            done = False
            error_occurred = False
            error_message = ""
            
            def handle_recognized(evt):
                """Handle recognized speech."""
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    result_data = {
                        'text': evt.result.text,
                        'offset': evt.result.offset / 10000000,  # Convert to seconds
                        'duration': evt.result.duration / 10000000
                    }
                    
                    # Add speaker info if available
                    if enable_diarization:
                        speaker_id = evt.result.properties.get(
                            speechsdk.PropertyId.SpeechServiceResponse_JsonResult
                        )
                        if speaker_id:
                            try:
                                json_result = json.loads(speaker_id)
                                result_data['speaker'] = json_result.get('SpeakerId', 'Unknown')
                            except:
                                pass
                    
                    all_results.append(result_data)
                    full_transcript.append(evt.result.text)
                    
                    # Update progress
                    progress_msg = f"Transcribing: {len(full_transcript)} segments"
                    if enable_diarization and 'speaker' in result_data:
                        progress_msg += f" (Speaker {result_data['speaker']})"
                    
                    self._log(progress_msg, "info")
                    if self.progress_callback:
                        # Rough progress estimate (can't know total duration upfront)
                        percent = min(95, len(full_transcript) * 2)
                        self.progress_callback.update(percent, progress_msg)
            
            def handle_canceled(evt):
                """Handle cancellation."""
                nonlocal error_occurred, error_message, done
                
                cancellation = evt.result.cancellation_details
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    error_occurred = True
                    error_message = f"Azure Speech error: {cancellation.error_details}"
                    self._log(error_message, "error")
                
                done = True
            
            def handle_session_stopped(evt):
                """Handle session stopped."""
                nonlocal done
                done = True
            
            # Connect callbacks
            speech_recognizer.recognized.connect(handle_recognized)
            speech_recognizer.canceled.connect(handle_canceled)
            speech_recognizer.session_stopped.connect(handle_session_stopped)
            
            # Start continuous recognition
            self._log("Starting transcription...", "info")
            if self.progress_callback:
                self.progress_callback.update(5, "Connecting to Azure Speech Service...")
            
            speech_recognizer.start_continuous_recognition()
            
            # Wait for completion
            start_time = time.time()
            while not done:
                time.sleep(0.5)
                
                # Timeout after 30 minutes
                if time.time() - start_time > 1800:
                    error_occurred = True
                    error_message = "Transcription timeout (30 minutes)"
                    break
            
            # Stop recognition
            speech_recognizer.stop_continuous_recognition()
            
            # Check for errors
            if error_occurred:
                self._log(error_message, "error")
                return False, "", error_message
            
            if not all_results:
                error_msg = "No speech detected in audio file"
                self._log(error_msg, "warning")
                return False, "", error_msg
            
            # Save transcript (plain text)
            transcript_text = "\n\n".join(full_transcript)
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            self._log(f"Saved transcript: {transcript_path}", "info")
            
            # Save detailed JSON with timestamps
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            
            self._log(f"Saved detailed JSON: {json_path}", "info")
            
            # Final progress update
            if self.progress_callback:
                self.progress_callback.update(100, f"Transcription complete: {len(all_results)} segments")
            
            success_msg = f"Transcribed {len(all_results)} segments successfully"
            self._log(success_msg, "success")
            
            return True, transcript_path, success_msg
        
        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            self._log(error_msg, "error")
            if self.progress_callback:
                self.progress_callback.error(error_msg, e)
            return False, "", error_msg
    
    def _log(self, message, level="info"):
        """Log message to callback."""
        if self.progress_callback:
            if level == "info":
                self.progress_callback.log(message)
            elif level == "warning":
                self.progress_callback.log(f"[WARNING] {message}")
            elif level == "error":
                self.progress_callback.log(f"[ERROR] {message}")
            elif level == "success":
                self.progress_callback.log(f"[SUCCESS] {message}")
