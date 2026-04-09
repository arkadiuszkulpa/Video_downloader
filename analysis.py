import os
import requests
import urllib3
import sys
import argparse

# Disable SSL warnings for corporate proxy compatibility
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_transcript(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def split_into_chunks(text, max_tokens=3000, overlap=200):
    """
    Split text into overlapping chunks to preserve context across boundaries.
    This helps maintain topic continuity in summaries.
    """
    # Split by lines for better control
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        line_length = len(line)

        # If adding this line exceeds max_tokens, save current chunk and start new one
        if current_length + line_length > max_tokens and current_chunk:
            chunks.append('\n'.join(current_chunk))

            # Create overlap by keeping last portion of current chunk
            overlap_text = '\n'.join(current_chunk)
            if len(overlap_text) > overlap:
                # Find a good split point within overlap range
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

def build_headers(api_key, provider):
    """Build HTTP headers based on API provider."""
    headers = {"content-type": "application/json"}
    
    if provider == 'anthropic':
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
    elif provider in ['databricks', 'openai']:
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        # Default to Authorization header
        headers["Authorization"] = f"Bearer {api_key}"
    
    return headers

def build_payload(prompt, max_tokens, model_name, provider):
    """Build request payload based on API provider."""
    return {
        "model": model_name,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }

def extract_response(response_json, provider):
    """Extract text response based on API provider format."""
    # Check for errors
    if 'error' in response_json:
        error_detail = response_json['error']
        if isinstance(error_detail, dict):
            error_msg = error_detail.get('message', str(error_detail))
        else:
            error_msg = str(error_detail)
        raise Exception(f"API Error: {error_msg}")
    
    # Extract content based on provider
    if provider == 'anthropic':
        if 'content' not in response_json:
            raise Exception(f"Unexpected API response (missing 'content'): {response_json}")
        return response_json['content'][0]['text']
    
    elif provider in ['databricks', 'openai', 'unknown']:
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

def tidy_chunk(chunk, api_key, endpoint, provider, model_name):
    system_message = (
        "Clean up this transcript: fix typos, add punctuation, and create proper sentences. "
        "Keep it concise - don't expand or elaborate, just clean the existing text."
    )
    headers = build_headers(api_key, provider)
    payload = build_payload(f"{system_message}\n{chunk}", 1024, model_name, provider)
    
    response = requests.post(endpoint, json=payload, headers=headers, verify=False)
    response_json = response.json()

    return extract_response(response_json, provider)

def summarize_chunk(chunk, api_key, endpoint, provider, model_name, chunk_label=None):
    prompt = (
        "Summarize the key points from this transcript chunk. "
        "Be concise - extract only the main ideas and important details. "
        "Use bullet points or brief paragraphs."
    )
    if chunk_label is not None:
        prompt += f"\n\n[{chunk_label}]"
    prompt += f"\n\nTranscript:\n{chunk}"

    headers = build_headers(api_key, provider)
    payload = build_payload(prompt, 2048, model_name, provider)

    response = requests.post(endpoint, json=payload, headers=headers, verify=False)
    response_json = response.json()

    return extract_response(response_json, provider)

def iterative_summary(summaries, api_key, endpoint, provider, model_name):
    prompt = (
        "Combine these summaries into one concise final summary. "
        "Remove redundancy, keep only key points, and organize by topic. "
        "Aim for a summary that's shorter than the original transcript.\n\n"
        "Chunk Summaries:\n\n"
        + "\n\n".join(summaries)
    )
    headers = build_headers(api_key, provider)
    payload = build_payload(prompt, 4096, model_name, provider)
    
    response = requests.post(endpoint, json=payload, headers=headers, verify=False)
    response_json = response.json()

    return extract_response(response_json, provider)

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze transcript with comprehensive topic-based summaries",
        epilog="Supports Anthropic, Databricks, OpenAI, and other compatible APIs"
    )
    parser.add_argument(
        'transcript',
        nargs='?',
        default=os.path.join("dump", "transcript.txt"),
        help='Path to transcript file (default: dump/transcript.txt)'
    )
    
    # Authentication options
    auth_group = parser.add_mutually_exclusive_group()
    auth_group.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Direct API key (supports Anthropic, Databricks, OpenAI, etc.)'
    )
    auth_group.add_argument(
        '--secret-name',
        type=str,
        default=None,
        help='AWS Secrets Manager secret name (default: env AWS_SECRET_NAME or "anthropic/default")'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        default=None,
        help='AWS region for Secrets Manager (default: env AWS_REGION or "eu-west-2")'
    )
    
    # API configuration
    parser.add_argument(
        '--endpoint',
        type=str,
        default="https://api.anthropic.com/v1/messages",
        help='API endpoint URL (default: Anthropic API)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default="claude-opus-4-5-20251101",
        help='Model name (default: claude-opus-4-5-20251101)'
    )
    parser.add_argument(
        '--provider',
        type=str,
        choices=['anthropic', 'databricks', 'openai', 'auto'],
        default='auto',
        help='API provider type (default: auto-detect from endpoint)'
    )
    
    return parser.parse_args()

def get_api_key(secret_name=None, region_name=None):
    """Get API key from AWS Secrets Manager"""
    from apikey import get_secret
    return get_secret(secret_name=secret_name, region_name=region_name)

def main():
    args = parse_args()

    print(f"Analyzing transcript: {args.transcript}")

    # Get API key
    if args.api_key:
        api_key = args.api_key
        print("Using direct API key authentication")
    else:
        try:
            api_key = get_api_key(secret_name=args.secret_name, region_name=args.region)
            print("Using AWS Secrets Manager authentication")
        except Exception as e:
            print(f"Error: Could not retrieve API key from AWS Secrets Manager: {e}")
            print("\nPlease either:")
            print("  1. Use --api-key to provide a direct API key, or")
            print("  2. Configure AWS credentials with: aws configure")
            print(f"\nFor AWS Secrets Manager:")
            print(f"  Secret name: {args.secret_name or os.environ.get('AWS_SECRET_NAME', 'anthropic/default')}")
            print(f"  Region: {args.region or os.environ.get('AWS_REGION', 'eu-west-2')}")
            return

    # Detect provider
    if args.provider == 'auto':
        endpoint_lower = args.endpoint.lower()
        if 'anthropic.com' in endpoint_lower:
            provider = 'anthropic'
        elif 'databricks' in endpoint_lower or 'azuredatabricks' in endpoint_lower:
            provider = 'databricks'
        elif 'openai.com' in endpoint_lower or 'azure.com' in endpoint_lower:
            provider = 'openai'
        else:
            provider = 'unknown'
    else:
        provider = args.provider
    
    print(f"API Provider: {provider}")
    print(f"Endpoint: {args.endpoint}")
    print(f"Model: {args.model}\n")

    endpoint = args.endpoint
    model_name = args.model
    transcript = load_transcript(args.transcript)

    print(f"Splitting transcript into overlapping chunks...")
    chunks = split_into_chunks(transcript)
    print(f"Created {len(chunks)} chunks for analysis\n")

    chunk_summaries = []
    for idx, chunk in enumerate(chunks):
        label = f"Chunk {idx+1}/{len(chunks)}"
        print(f"Processing {label}...")
        tidy = tidy_chunk(chunk, api_key, endpoint, provider, model_name)
        summary = summarize_chunk(tidy, api_key, endpoint, provider, model_name, chunk_label=label)
        chunk_summaries.append(f"{label}: {summary}")

    print("\nGenerating final comprehensive summary...\n")
    final_summary = iterative_summary(chunk_summaries, api_key, endpoint, provider, model_name)

    # Save output to file
    output_basename = os.path.splitext(os.path.basename(args.transcript))[0]
    output_path = os.path.join("dump", f"{output_basename}_analysis.txt")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE TOPIC-BASED SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(final_summary)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("CHUNK-BY-CHUNK SUMMARIES\n")
        f.write("=" * 80 + "\n\n")
        for s in chunk_summaries:
            f.write(s + "\n\n")

    print(f"Analysis saved to: {output_path}\n")
    print("=" * 80)
    print("FINAL SUMMARY:")
    print("=" * 80)
    print(final_summary)

if __name__ == "__main__":
    main()