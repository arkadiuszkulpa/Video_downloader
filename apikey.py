# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError
import os


def get_secret(secret_name=None, region_name=None):
    """
    Retrieve a secret from AWS Secrets Manager.

    Args:
        secret_name: Name of the secret in AWS Secrets Manager.
                    Defaults to environment variable AWS_SECRET_NAME or "anthropic/default"
        region_name: AWS region where the secret is stored.
                    Defaults to environment variable AWS_REGION or "eu-west-2"

    Returns:
        str: The secret value (API key)

    Raises:
        ClientError: If the secret cannot be retrieved
    """
    # Use provided values, fall back to environment variables, then to defaults
    if secret_name is None:
        secret_name = os.environ.get('AWS_SECRET_NAME', 'anthropic/default')

    if region_name is None:
        region_name = os.environ.get('AWS_REGION', 'eu-west-2')

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return secret  # Return the secret string (API key)
