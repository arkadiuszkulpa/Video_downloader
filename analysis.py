import os
import requests
from apikey import get_secret

def load_transcript(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def split_into_chunks(text, max_tokens=1500):
    # Simple split by sentences, paragraphs, or custom logic
    paragraphs = text.split('\n\n')
    chunks = []
    chunk = ""
    for para in paragraphs:
        if len(chunk) + len(para) < max_tokens:
            chunk += para + "\n\n"
        else:
            chunks.append(chunk.strip())
            chunk = para + "\n\n"
    if chunk:
        chunks.append(chunk.strip())
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
    prompt = f"Summarize this text chunk"
    if chunk_label is not None:
        prompt += f" ({chunk_label})"
    prompt += f":\n{chunk}"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['content'][0]['text']

def iterative_summary(summaries, api_key, endpoint):
    prompt = (
        "Here are summaries of transcript chunks from a long conversation. "
        "Please create a final summary that represents all chunks equally, "
        "without focusing only on the most important or salient points. "
        "Ensure the final summary covers the breadth of topics and details from each chunk.\n\n"
        + "\n\n".join(summaries)
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
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()['content'][0]['text']

def main():
    transcript_path = os.path.join("dump", "transcript.txt")
    api_key = get_secret()  # Get API key from Secrets Manager
    endpoint = "https://api.anthropic.com/v1/messages"
    transcript = load_transcript(transcript_path)
    chunks = split_into_chunks(transcript)
    chunk_summaries = []
    for idx, chunk in enumerate(chunks):
        label = f"Chunk {idx+1}"
        tidy = tidy_chunk(chunk, api_key, endpoint)
        summary = summarize_chunk(tidy, api_key, endpoint, chunk_label=label)
        chunk_summaries.append(f"{label}: {summary}")
    final_summary = iterative_summary(chunk_summaries, api_key, endpoint)
    print("Chunk Summaries:")
    for s in chunk_summaries:
        print(s)
    print("\nFinal Summary:", final_summary)

if __name__ == "__main__":
    main()