"""Input validation functions for GUI."""

import os
import re
from urllib.parse import urlparse


def validate_url(url):
    """
    Validate URL format.

    Args:
        url (str): URL to validate

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url = url.strip()

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format. Must include protocol (http:// or https://)"

        if result.scheme not in ['http', 'https']:
            return False, "URL must use HTTP or HTTPS protocol"

        return True, None

    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def validate_api_key(api_key, provider=None):
    """
    Validate API key format for various providers.

    Args:
        api_key (str): API key to validate
        provider (str, optional): Provider name for specific validation
                                 ('anthropic', 'databricks', 'openai', or None for generic)

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"

    api_key = api_key.strip()

    # Provider-specific validation
    if provider and provider.lower() == 'anthropic':
        if not api_key.startswith('sk-ant-'):
            return False, "Anthropic API keys must start with 'sk-ant-'"
    elif provider and provider.lower() == 'databricks':
        if not api_key.startswith('dapi'):
            return False, "Databricks API keys must start with 'dapi'"
    elif provider and provider.lower() == 'openai':
        if not api_key.startswith('sk-'):
            return False, "OpenAI API keys must start with 'sk-'"
    
    # Generic validation (no specific provider)
    if len(api_key) < 10:
        return False, "API key appears too short (minimum 10 characters)"

    return True, None


def validate_file_exists(file_path):
    """
    Check if file exists and is accessible.

    Args:
        file_path (str): Path to file

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not file_path or not file_path.strip():
        return False, "File path cannot be empty"

    file_path = file_path.strip()

    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    if not os.path.isfile(file_path):
        return False, f"Path is not a file: {file_path}"

    if not os.access(file_path, os.R_OK):
        return False, f"File is not readable: {file_path}"

    return True, None


def validate_directory(dir_path, check_writable=True):
    """
    Check if directory exists and is accessible.

    Args:
        dir_path (str): Path to directory
        check_writable (bool): Also check if directory is writable

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not dir_path or not dir_path.strip():
        return False, "Directory path cannot be empty"

    dir_path = dir_path.strip()

    if not os.path.exists(dir_path):
        # Try to create it
        try:
            os.makedirs(dir_path, exist_ok=True)
            return True, None
        except Exception as e:
            return False, f"Cannot create directory: {str(e)}"

    if not os.path.isdir(dir_path):
        return False, f"Path is not a directory: {dir_path}"

    if check_writable and not os.access(dir_path, os.W_OK):
        return False, f"Directory is not writable: {dir_path}"

    return True, None
