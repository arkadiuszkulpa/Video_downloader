"""Transcript analysis with Claude AI and progress callback support."""

import os
import requests


class Analyzer:
    """
    Transcript analyzer using Claude API with progress callbacks.

    Supports:
    - Chunked transcript processing with overlap
    - Concise summaries
    - Progress reporting per chunk
    - Configurable API endpoint
    - Direct API key input (no AWS dependency in core logic)
    """

    DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-opus-4-5-20251101"

    def __init__(self, progress_callback=None):
        """
        Initialize analyzer.

        Args:
            progress_callback (ProgressCallback, optional): Callback for progress updates
        """
        self.progress_callback = progress_callback

    def analyze(self, transcript_file, output_dir, api_key, endpoint=None,
                max_tokens=3000, overlap=200):
        """
        Analyze transcript file and generate summary.

        Args:
            transcript_file (str): Path to transcript file
            output_dir (str): Output directory for analysis
            api_key (str): Anthropic API key
            endpoint (str, optional): API endpoint (default: Anthropic API)
            max_tokens (int): Maximum tokens per chunk
            overlap (int): Overlap between chunks in characters

        Returns:
            tuple: (success: bool, analysis_file: str, message: str)
        """
        try:
            # Validate inputs
            if not os.path.exists(transcript_file):
                return False, "", f"Transcript file not found: {transcript_file}"

            if not os.path.isfile(transcript_file):
                return False, "", f"Path is not a file: {transcript_file}"

            if not api_key or not api_key.strip():
                return False, "", "API key is required"

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Use default endpoint if not provided
            if not endpoint:
                endpoint = self.DEFAULT_ENDPOINT

            # Load transcript
            self._log(f"Loading transcript: {transcript_file}", "info")
            transcript = self._load_transcript(transcript_file)

            # Split into chunks
            self._log("Splitting transcript into overlapping chunks...", "info")
            chunks = self._split_into_chunks(transcript, max_tokens, overlap)
            self._log(f"Created {len(chunks)} chunks for analysis", "info")

            # Process each chunk
            chunk_summaries = []
            for idx, chunk in enumerate(chunks):
                label = f"Chunk {idx+1}/{len(chunks)}"
                self._log(f"Processing {label}...", "info")

                # Update progress
                if self.progress_callback:
                    self.progress_callback.update(
                        'analyze', idx + 1, len(chunks),
                        f"Processing {label}"
                    )

                # Tidy and summarize chunk
                tidy = self._tidy_chunk(chunk, api_key, endpoint)
                summary = self._summarize_chunk(tidy, api_key, endpoint, chunk_label=label)
                chunk_summaries.append(f"{label}: {summary}")

            # Generate final summary
            self._log("Generating final comprehensive summary...", "info")
            final_summary = self._iterative_summary(chunk_summaries, api_key, endpoint)

            # Save output
            output_basename = os.path.splitext(os.path.basename(transcript_file))[0]
            analysis_file = os.path.join(output_dir, f"{output_basename}_analysis.txt")

            self._save_analysis(analysis_file, final_summary, chunk_summaries)

            self._log(f"Analysis saved to: {analysis_file}", "info")

            return True, analysis_file, "Analysis complete"

        except Exception as e:
            error_msg = f"Analysis error: {str(e)}"
            self._log(error_msg, "error")
            if self.progress_callback:
                self.progress_callback.error(error_msg, e)
            return False, "", error_msg

    def _load_transcript(self, filepath):
        """Load transcript from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _split_into_chunks(self, text, max_tokens=3000, overlap=200):
        """
        Split text into overlapping chunks to preserve context.

        Args:
            text (str): Text to split
            max_tokens (int): Maximum tokens per chunk
            overlap (int): Overlap in characters

        Returns:
            list: List of text chunks
        """
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line)

            # If adding this line exceeds max_tokens, save current chunk
            if current_length + line_length > max_tokens and current_chunk:
                chunks.append('\n'.join(current_chunk))

                # Create overlap by keeping last portion of current chunk
                overlap_text = '\n'.join(current_chunk)
                if len(overlap_text) > overlap:
                    # Find split point within overlap range
                    overlap_lines = []
                    overlap_length = 0
                    for l in reversed(current_chunk):
                        if overlap_length + len(l) < overlap:
                            overlap_lines.insert(0, l)
                            overlap_length += len(l)
                        else:
                            break
                    current_chunk = overlap_lines
                    current_length = overlap_length
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(line)
            current_length += line_length

        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def _tidy_chunk(self, chunk, api_key, endpoint):
        """
        Clean up transcript chunk (fix typos, add punctuation).

        Args:
            chunk (str): Text chunk to tidy
            api_key (str): API key
            endpoint (str): API endpoint

        Returns:
            str: Tidied text
        """
        system_message = (
            "Clean up this transcript: fix typos, add punctuation, and create proper sentences. "
            "Keep it concise - don't expand or elaborate, just clean the existing text."
        )

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.DEFAULT_MODEL,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": f"{system_message}\n{chunk}"}
            ]
        }

        response = requests.post(endpoint, json=payload, headers=headers)
        response_json = response.json()

        # Check for errors
        if 'error' in response_json:
            raise Exception(f"API Error: {response_json['error']}")

        if 'content' not in response_json:
            raise Exception(f"Unexpected API response: {response_json}")

        return response_json['content'][0]['text']

    def _summarize_chunk(self, chunk, api_key, endpoint, chunk_label=None):
        """
        Summarize transcript chunk.

        Args:
            chunk (str): Text chunk to summarize
            api_key (str): API key
            endpoint (str): API endpoint
            chunk_label (str, optional): Label for this chunk

        Returns:
            str: Summary text
        """
        prompt = (
            "Summarize the key points from this transcript chunk. "
            "Be concise - extract only the main ideas and important details. "
            "Use bullet points or brief paragraphs."
        )

        if chunk_label is not None:
            prompt += f"\n\n[{chunk_label}]"
        prompt += f"\n\nTranscript:\n{chunk}"

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.DEFAULT_MODEL,
            "max_tokens": 2048,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(endpoint, json=payload, headers=headers)
        response_json = response.json()

        if 'error' in response_json:
            raise Exception(f"API Error: {response_json['error']}")

        if 'content' not in response_json:
            raise Exception(f"Unexpected API response: {response_json}")

        return response_json['content'][0]['text']

    def _iterative_summary(self, summaries, api_key, endpoint):
        """
        Combine chunk summaries into final summary.

        Args:
            summaries (list): List of chunk summaries
            api_key (str): API key
            endpoint (str): API endpoint

        Returns:
            str: Final combined summary
        """
        prompt = (
            "Combine these summaries into one concise final summary. "
            "Remove redundancy, keep only key points, and organize by topic. "
            "Aim for a summary that's shorter than the original transcript.\n\n"
            "Chunk Summaries:\n\n"
            + "\n\n".join(summaries)
        )

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.DEFAULT_MODEL,
            "max_tokens": 4096,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(endpoint, json=payload, headers=headers)
        response_json = response.json()

        if 'error' in response_json:
            raise Exception(f"API Error: {response_json['error']}")

        if 'content' not in response_json:
            raise Exception(f"Unexpected API response: {response_json}")

        return response_json['content'][0]['text']

    def _save_analysis(self, output_path, final_summary, chunk_summaries):
        """
        Save analysis to file.

        Args:
            output_path (str): Output file path
            final_summary (str): Final summary text
            chunk_summaries (list): List of chunk summaries
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("FINAL SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(final_summary)
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("CHUNK-BY-CHUNK SUMMARIES\n")
            f.write("=" * 80 + "\n\n")
            for s in chunk_summaries:
                f.write(s + "\n\n")

    def _log(self, message, level='info'):
        """Send log message via callback or print."""
        if self.progress_callback:
            self.progress_callback.log(message, level)
        else:
            print(f"[{level.upper()}] {message}")
