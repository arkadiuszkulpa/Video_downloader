"""Authentication manager supporting AWS Secrets Manager and direct API key input."""

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthManager:
    """
    Unified authentication manager supporting two modes:
    1. AWS Secrets Manager (existing functionality)
    2. Direct API key input (for environments without AWS)
    """

    @staticmethod
    def get_api_key(method='aws', **kwargs):
        """
        Retrieve API key using specified authentication method.

        Args:
            method (str): Authentication method - 'aws' or 'direct'
            **kwargs: Method-specific parameters
                For 'aws': secret_name, region_name
                For 'direct': api_key

        Returns:
            str: API key

        Raises:
            AuthenticationError: If authentication fails
            ValueError: If method is invalid or required parameters are missing

        Examples:
            # AWS Secrets Manager
            api_key = AuthManager.get_api_key(
                method='aws',
                secret_name='anthropic/other',
                region_name='eu-west-2'
            )

            # Direct API key
            api_key = AuthManager.get_api_key(
                method='direct',
                api_key='sk-ant-api03-...'
            )
        """
        if method == 'aws':
            return AuthManager._get_api_key_from_aws(**kwargs)
        elif method == 'direct':
            return AuthManager._get_api_key_direct(**kwargs)
        else:
            raise ValueError(f"Unknown authentication method: {method}. Use 'aws' or 'direct'.")

    @staticmethod
    def _get_api_key_from_aws(secret_name=None, region_name=None):
        """
        Retrieve API key from AWS Secrets Manager.

        Args:
            secret_name (str, optional): AWS secret name. If None, uses environment variable.
            region_name (str, optional): AWS region. If None, uses environment variable.

        Returns:
            str: API key from AWS Secrets Manager

        Raises:
            AuthenticationError: If retrieval from AWS fails
        """
        try:
            from apikey import get_secret
            api_key = get_secret(secret_name=secret_name, region_name=region_name)
            if not api_key:
                raise AuthenticationError("AWS Secrets Manager returned empty API key")
            return api_key
        except ImportError:
            raise AuthenticationError("apikey module not found. Cannot use AWS authentication.")
        except Exception as e:
            raise AuthenticationError(f"Failed to retrieve API key from AWS: {str(e)}")

    @staticmethod
    def _get_api_key_direct(api_key=None):
        """
        Use directly provided API key.

        Args:
            api_key (str): The API key to use

        Returns:
            str: Validated API key

        Raises:
            ValueError: If API key is missing or invalid
        """
        if not api_key:
            raise ValueError("API key is required for direct authentication")

        api_key = api_key.strip()

        if not api_key:
            raise ValueError("API key cannot be empty or whitespace")

        # Basic validation - Anthropic API keys start with 'sk-ant-'
        if not api_key.startswith('sk-ant-'):
            raise ValueError("Invalid API key format. Anthropic API keys should start with 'sk-ant-'")

        return api_key
