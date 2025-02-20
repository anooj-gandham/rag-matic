import logging
import os

import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError

# Initialize Logger
logger = logging.getLogger(__name__)

# Load environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


def modify_file_name(file_name):
    """
    Modifies the file name by replacing spaces with underscores.

    :param file_name: Original file name
    :return: Modified file name with spaces replaced by underscores
    """
    return file_name.replace(" ", "_")

def upload_file_to_s3(file, file_name, bucket=S3_BUCKET_NAME, acl="public-read"):
    """
    Uploads a file to an S3 bucket.

    :param file: File object (Django InMemoryUploadedFile or open file)
    :param file_name: File name to store in S3
    :param bucket: S3 bucket name
    :param acl: Access control list setting for the file (default: 'public-read')
    :return: File URL if successful, None otherwise
    """
    try:
        file_name = modify_file_name(file_name)
        s3_client.upload_fileobj(file, bucket, file_name)
    except NoCredentialsError:
        logger.exception("AWS credentials not available.")
        return None
    except ClientError:
        logger.exception("Error uploading file")  # Ruff-compliant logging
        return None
    else:
        return f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{file_name}"


def delete_file_from_s3(file_name, bucket=S3_BUCKET_NAME):
    """
    Deletes a file from an S3 bucket.

    :param file_name: Name of the file to delete in S3
    :param bucket: S3 bucket name
    :return: True if successful, False otherwise
    """
    try:
        s3_client.delete_object(Bucket=bucket, Key=file_name)
    except NoCredentialsError:
        logger.exception("AWS credentials not available.")
        return False
    except ClientError:
        logger.exception("Error deleting file")  # Ruff-compliant logging
        return False
    else:
        return True
