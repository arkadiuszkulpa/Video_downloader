# Using Databricks Served Models for Transcript Analysis

## Overview

The analyzer now supports multiple API providers including:
- **Anthropic** (Claude API)
- **Databricks** (Served Models with OpenAI-compatible endpoints)
- **OpenAI** (GPT models)
- **Any OpenAI-compatible API**

**Note:** SSL certificate verification is automatically disabled to support corporate proxy environments. This is the same approach used for video downloads and transcription.

## Databricks Setup

### 1. Get Your Databricks API Key

From your Databricks workspace:
1. Go to **User Settings** → **Access Tokens**
2. Generate a new token
3. Copy the token (starts with `dapi...`)

### 2. Get Your Model Serving Endpoint

1. Go to **Machine Learning** → **Serving**
2. Find your served model
3. Copy the **Endpoint URL** (e.g., `https://[workspace].databricks.com/serving-endpoints/[model-name]/invocations`)

## Using with GUI

### Analysis Tab

1. **Authentication Method**: Select "Direct API Key"
2. **API Key**: Paste your Databricks token (e.g., `dapi1234567890abcdef...`)
3. **Endpoint URI**: Paste your Databricks serving endpoint
4. **Model Name**: Enter the model name (e.g., `databricks-meta-llama-3-70b-instruct` or your custom model)

Example configuration:
```
API Key: dapi1234567890abcdef12345678...
Endpoint: https://[workspace].databricks.com/serving-endpoints/llama-3-70b/invocations
Model Name: databricks-meta-llama-3-70b-instruct
```

### Pipeline Tab

Same fields as above - the analyzer will auto-detect Databricks from the endpoint URL.

## Using Programmatically

```python
from core.analyzer import Analyzer

# Initialize analyzer
analyzer = Analyzer()

# Databricks configuration
api_key = "dapi1234567890abcdef..."
endpoint = "https://[workspace].databricks.com/serving-endpoints/[model]/invocations"
model_name = "databricks-meta-llama-3-70b-instruct"

# Set the model
analyzer.DEFAULT_MODEL = model_name

# Run analysis
success, output_file, message = analyzer.analyze(
    transcript_file="dump/transcript.txt",
    output_dir="dump",
    api_key=api_key,
    endpoint=endpoint,
    api_provider="databricks"  # Optional - auto-detects from endpoint
)

print(f"Success: {success}")
print(f"Output: {output_file}")
```

## Supported Databricks Models

### Foundation Models
- `databricks-meta-llama-3-1-70b-instruct`
- `databricks-meta-llama-3-1-405b-instruct`
- `databricks-dbrx-instruct`
- `databricks-mixtral-8x7b-instruct`

### Custom Fine-tuned Models
Any model you've deployed to a serving endpoint will work as long as it supports the OpenAI-compatible API format.

## API Format Differences

| Provider | Auth Header | Request Format | Response Format |
|----------|-------------|----------------|-----------------|
| Anthropic | `x-api-key: sk-ant-...` | `content` array | `content[0].text` |
| Databricks | `Authorization: Bearer dapi...` | OpenAI-compatible | `choices[0].message.content` |
| OpenAI | `Authorization: Bearer sk-...` | OpenAI format | `choices[0].message.content` |

The analyzer automatically handles these differences based on the endpoint URL.

## Auto-Detection

The analyzer auto-detects the provider from your endpoint:

```python
# These endpoints auto-detect as Databricks
"https://adb-123456.databricks.com/..."
"https://[workspace].azuredatabricks.net/..."

# This auto-detects as Anthropic
"https://api.anthropic.com/v1/messages"

# This auto-detects as OpenAI
"https://api.openai.com/v1/chat/completions"
```

You can override auto-detection by specifying `api_provider` explicitly.

## Troubleshooting

### Error: Invalid API key format
**Old behavior:** Rejected non-Anthropic keys
**New behavior:** Accepts any key ≥10 characters

### Error: Unexpected API response format
**Cause:** Response doesn't match expected format
**Solution:** 
1. Check your endpoint URL is correct
2. Verify the model is deployed and running
3. Check Databricks serving logs for errors

### Error: 401 Unauthorized
**Cause:** Invalid or expired API token
**Solution:** Generate a new token in Databricks User Settings

### Error: 404 Not Found
**Cause:** Endpoint URL is incorrect
**Solution:** 
1. Verify the serving endpoint exists
2. Check the exact URL from Databricks Serving page
3. Ensure `/invocations` is appended to the endpoint

### Error: SSL Certificate Verification Failed
**Cause:** Corporate proxy with self-signed certificates
**Solution:** ✅ Already handled automatically
- The analyzer disables SSL verification by default
- This is the same SSL bypass used for downloads and transcription
- No additional configuration needed

### Model not responding or slow
**Cause:** Databricks may need to warm up the model
**Solution:** 
1. First request may be slow (cold start)
2. Subsequent requests will be faster
3. Consider enabling serverless compute for instant scaling

## Cost Comparison

| Provider | Model | Cost/1M tokens (input) | Cost/1M tokens (output) |
|----------|-------|----------------------|------------------------|
| Anthropic | Claude Opus 4.5 | $15 | $75 |
| Databricks | Llama 3.1 70B | ~$1-3* | ~$1-3* |
| OpenAI | GPT-4 Turbo | $10 | $30 |

*Databricks pricing varies by workspace type and commit level

## Best Practices

1. **Model Selection**
   - Use Llama 3.1 70B for cost-effective analysis
   - Use larger models (405B) only for complex analysis
   - Test with smaller models first

2. **Token Limits**
   - Databricks models typically support 4K-128K context
   - Adjust `max_tokens` parameter based on your model
   - Monitor token usage in Databricks serving metrics

3. **Rate Limiting**
   - Databricks has per-endpoint rate limits
   - Consider batch processing for large workloads
   - Monitor throughput in serving dashboard

4. **Security**
   - Store API keys in environment variables or AWS Secrets Manager
   - Rotate tokens regularly
   - Use workspace access controls

## Example: Complete Workflow

```powershell
# 1. Set environment (if using conda/venv)
conda activate fabric

# 2. Download video (with Zoom cookies if needed)
$env:SSL_CERT_FILE=""; python main.py "https://zoom.us/rec/play/..."

# 3. Transcribe (with SSL bypass if needed)
$env:SSL_CERT_FILE=""; python transcribe.py "dump/video.mp4"

# 4. Analyze with Databricks
python analysis.py "dump/video_transcript.txt" `
    --api-key "dapi1234567890..." `
    --endpoint "https://workspace.databricks.com/serving-endpoints/llama-3-70b/invocations" `
    --model "databricks-meta-llama-3-70b-instruct"
```

## Advanced: Custom Headers

For providers requiring custom headers, modify `_build_headers()` in [core/analyzer.py](core/analyzer.py):

```python
def _build_headers(self, api_key):
    headers = {"content-type": "application/json"}
    
    if self.api_provider == 'custom':
        headers["X-Custom-Auth"] = api_key
        headers["X-Custom-Header"] = "value"
    
    return headers
```

## Support Matrix

| Feature | Anthropic | Databricks | OpenAI | Generic |
|---------|-----------|------------|--------|---------|
| Auto-detection | ✅ | ✅ | ✅ | ⚠️ Manual |
| Streaming | ❌ | ❌ | ❌ | ❌ |
| Function calling | ❌ | ❌ | ❌ | ❌ |
| Vision | ❌ | ❌ | ❌ | ❌ |
| JSON mode | ❌ | ❌ | ❌ | ❌ |

Currently focused on text summarization and analysis workflows.
