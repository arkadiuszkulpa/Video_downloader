@echo off
REM Transcribe.bat - Wrapper script to set SSL bypass environment variables before running transcription

echo Setting SSL bypass environment variables...
set SSL_CERT_FILE=
set REQUESTS_CA_BUNDLE=
set CURL_CA_BUNDLE=
set NO_PROXY=*

echo Running transcription...
python transcribe.py %*
