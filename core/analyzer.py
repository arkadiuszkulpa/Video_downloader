"""Transcript analysis with Claude AI and progress callback support."""

import os
import requests
import urllib3

# Disable SSL warnings for corporate proxy compatibility
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Analyzer:
    """
    Transcript analyzer using Claude API with progress callbacks.

    Supports:
    - Chunked transcript processing with overlap
    - Concise summaries
    - Progress reporting per chunk
    - Configurable API endpoint
    - Direct API key input (no AWS dependency in core logic)
    - Multiple API providers (Anthropic, Databricks, OpenAI-compatible)
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
        self.api_provider = None  # Will be auto-detected or set explicitly

    def analyze(self, transcript_file, output_dir, api_key, endpoint=None,
                max_tokens=3000, overlap=200, api_provider=None):
        """
        Analyze transcript file and generate summary.

        Args:
            transcript_file (str): Path to transcript file
            output_dir (str): Output directory for analysis
            api_key (str): API key (supports Anthropic, Databricks, OpenAI-compatible)
            endpoint (str, optional): API endpoint (default: Anthropic API)
            max_tokens (int): Maximum tokens per chunk
            overlap (int): Overlap between chunks in characters
            api_provider (str, optional): API provider type ('anthropic', 'databricks', 'openai')
                                         If None, will auto-detect from endpoint

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
            
            # Auto-detect API provider from endpoint or use provided
            if api_provider:
                self.api_provider = api_provider.lower()
            else:
                self.api_provider = self._detect_provider(endpoint)
            
            self._log(f"Using API provider: {self.api_provider}", "info")

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

        headers = self._build_headers(api_key)

        payload = self._build_payload(
            prompt=f"{system_message}\n{chunk}",
            max_tokens=1024
        )

        response = requests.post(endpoint, json=payload, headers=headers, verify=False)
        response_json = response.json()

        # Extract response based on provider
        return self._extract_response(response_json)

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

        headers = self._build_headers(api_key)
        payload = self._build_payload(prompt=prompt, max_tokens=2048)

        response = requests.post(endpoint, json=payload, headers=headers, verify=False)
        response_json = response.json()

        return self._extract_response(response_json)

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

        headers = self._build_headers(api_key)
        payload = self._build_payload(prompt=prompt, max_tokens=4096)

        response = requests.post(endpoint, json=payload, headers=headers, verify=False)
        response_json = response.json()

        return self._extract_response(response_json)

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

    def _detect_provider(self, endpoint):
        """
        Auto-detect API provider from endpoint URL.
        
        Args:
            endpoint (str): API endpoint URL
            
        Returns:
            str: Provider name ('anthropic', 'databricks', 'openai', or 'unknown')
        """
        endpoint_lower = endpoint.lower()
        
        if 'anthropic.com' in endpoint_lower:
            return 'anthropic'
        elif 'databricks' in endpoint_lower or 'azuredatabricks' in endpoint_lower:
            return 'databricks'
        elif 'openai.com' in endpoint_lower or 'azure.com' in endpoint_lower:
            return 'openai'
        else:
            return 'unknown'
    
    def _build_headers(self, api_key):
        """
        Build HTTP headers based on API provider.
        
        Args:
            api_key (str): API key
            
        Returns:
            dict: HTTP headers
        """
        headers = {"content-type": "application/json"}
        
        if self.api_provider == 'anthropic':
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        elif self.api_provider == 'databricks':
            headers["Authorization"] = f"Bearer {api_key}"
        elif self.api_provider == 'openai':
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            # Default to Authorization header for unknown providers
            headers["Authorization"] = f"Bearer {api_key}"
        
        return headers
    
    def _build_payload(self, prompt, max_tokens):
        """
        Build request payload based on API provider.
        
        Args:
            prompt (str): Prompt text
            max_tokens (int): Maximum tokens
            
        Returns:
            dict: Request payload
        """
        if self.api_provider == 'anthropic':
            return {
                "model": self.DEFAULT_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
        elif self.api_provider in ['databricks', 'openai']:
            # OpenAI-compatible format (used by Databricks served models)
            return {
                "model": self.DEFAULT_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
        else:
            # Default to OpenAI-compatible format
            return {
                "model": self.DEFAULT_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
    
    def _extract_response(self, response_json):
        """
        Extract text response based on API provider format.
        
        Args:
            response_json (dict): API response JSON
            
        Returns:
            str: Extracted text
            
        Raises:
            Exception: If response contains errors or unexpected format
        """
        # Check for errors (common across providers)
        if 'error' in response_json:
            error_detail = response_json['error']
            if isinstance(error_detail, dict):
                error_msg = error_detail.get('message', str(error_detail))
            else:
                error_msg = str(error_detail)
            raise Exception(f"API Error: {error_msg}")
        
        # Extract content based on provider
        if self.api_provider == 'anthropic':
            if 'content' not in response_json:
                raise Exception(f"Unexpected API response (missing 'content'): {response_json}")
            return response_json['content'][0]['text']
        
        elif self.api_provider in ['databricks', 'openai']:
            # OpenAI-compatible format
            if 'choices' in response_json and len(response_json['choices']) > 0:
                choice = response_json['choices'][0]
                if 'message' in choice:
                    return choice['message']['content']
                elif 'text' in choice:
                    return choice['text']
            
            # Fallback: try Anthropic format
            if 'content' in response_json:
                if isinstance(response_json['content'], list):
                    return response_json['content'][0]['text']
                return response_json['content']
            
            raise Exception(f"Unexpected API response format: {response_json}")
        
        else:
            # Unknown provider - try common formats
            if 'choices' in response_json:
                return response_json['choices'][0]['message']['content']
            elif 'content' in response_json:
                return response_json['content'][0]['text']
            else:
                raise Exception(f"Unexpected API response format: {response_json}")

    def _log(self, message, level='info'):
        """Send log message via callback or print."""
        if self.progress_callback:
            self.progress_callback.log(message, level)
        else:
            print(f"[{level.upper()}] {message}")
