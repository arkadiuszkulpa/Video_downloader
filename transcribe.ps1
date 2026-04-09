# Transcribe.ps1 - PowerShell wrapper to set SSL bypass environment variables

Write-Host "Setting SSL bypass environment variables..." -ForegroundColor Yellow

$env:SSL_CERT_FILE = ""
$env:REQUESTS_CA_BUNDLE = ""
$env:CURL_CA_BUNDLE = ""
$env:NO_PROXY = "*"

Write-Host "Running transcription..." -ForegroundColor Green

# Pass all arguments to the Python script
python transcribe.py $args
