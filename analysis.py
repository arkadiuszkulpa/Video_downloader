import os
import requests
import sys
import argparse

def load_transcript(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def split_into_chunks(text, max_tokens=2000, overlap=500):
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

def tidy_chunk(chunk, api_key, endpoint):
    system_message = (
        "You are a helpful assistant. Tidy the following transcript chunk: "
        "remove typos, infer proper words where words have not been recognised by the transcription, "
        "add interpunction, create proper sentences, but do not change any of the meaning."
    )
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": f"{system_message}\n{chunk}"}
        ]
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['content'][0]['text']

def summarize_chunk(chunk, api_key, endpoint, chunk_label=None):
    prompt = (
        "Provide a comprehensive summary of this transcript chunk that covers ALL topics discussed. "
        "Do NOT reduce to only the most important points - include all subjects, themes, and details mentioned. "
        "Organize by topic if multiple topics are present. Maintain completeness over brevity."
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
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2048,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['content'][0]['text']

def iterative_summary(summaries, api_key, endpoint):
    prompt = (
        "Synthesize these chunk summaries into a comprehensive final summary organized by topics. "
        "Cover ALL topics mentioned across all chunks - do not filter to only highlights. "
        "The goal is breadth and completeness, not brevity. Group related topics together.\n\n"
        "Chunk Summaries:\n\n"
        + "\n\n".join(summaries)
    )
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['content'][0]['text']

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze transcript with comprehensive topic-based summaries"
    )
    parser.add_argument(
        'transcript',
        nargs='?',
        default=os.path.join("dump", "transcript.txt"),
        help='Path to transcript file (default: dump/transcript.txt)'
    )
    parser.add_argument(
        '--secret-name',
        type=str,
        default=None,
        help='AWS Secrets Manager secret name (default: env AWS_SECRET_NAME or "anthropic/default")'
    )
    parser.add_argument(
        '--region',
        type=str,
        default=None,
        help='AWS region (default: env AWS_REGION or "eu-west-2")'
    )
    return parser.parse_args()

def get_api_key(secret_name=None, region_name=None):
    """Get API key from AWS Secrets Manager"""
    from apikey import get_secret
    return get_secret(secret_name=secret_name, region_name=region_name)

def main():
    args = parse_args()

    print(f"Analyzing transcript: {args.transcript}")

    try:
        api_key = get_api_key(secret_name=args.secret_name, region_name=args.region)
    except Exception as e:
        print(f"Error: Could not retrieve API key from AWS Secrets Manager: {e}")
        print("\nPlease ensure your AWS credentials are configured correctly:")
        print("  aws configure")
        print(f"\nAnd that the secret exists in AWS Secrets Manager.")
        print(f"Secret name: {args.secret_name or os.environ.get('AWS_SECRET_NAME', 'anthropic/default')}")
        print(f"Region: {args.region or os.environ.get('AWS_REGION', 'eu-west-2')}")
        return

    endpoint = "https://api.anthropic.com/v1/messages"
    transcript = load_transcript(args.transcript)

    print(f"Splitting transcript into overlapping chunks...")
    chunks = split_into_chunks(transcript)
    print(f"Created {len(chunks)} chunks for analysis\n")

    chunk_summaries = []
    for idx, chunk in enumerate(chunks):
        label = f"Chunk {idx+1}/{len(chunks)}"
        print(f"Processing {label}...")
        tidy = tidy_chunk(chunk, api_key, endpoint)
        summary = summarize_chunk(tidy, api_key, endpoint, chunk_label=label)
        chunk_summaries.append(f"{label}: {summary}")

    print("\nGenerating final comprehensive summary...\n")
    final_summary = iterative_summary(chunk_summaries, api_key, endpoint)

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