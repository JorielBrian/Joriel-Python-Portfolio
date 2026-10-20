import os
import uuid

import boto3


# Neon Object Storage credentials stay on the backend. The bucket remains
# private; public downloads are streamed through the FastAPI endpoint.
AWS_ENDPOINT_URL_S3 = os.environ["AWS_ENDPOINT_URL_S3"]
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = os.environ["AWS_REGION"]

# The bucket name is separate from the endpoint and credentials.
# Configure NEON_STORAGE_BUCKET with the exact name of your Neon bucket.
NEON_STORAGE_BUCKET = os.environ["NEON_STORAGE_BUCKET"]

_client = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT_URL_S3,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


def upload_file(file_bytes: bytes, original_filename: str, content_type: str) -> str:
    """Upload a file to the private bucket and return its object key."""
    key = f"resume/{uuid.uuid4().hex}.pdf"

    _client.put_object(
        Bucket=NEON_STORAGE_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key


def download_file(key: str) -> bytes:
    """Read a private object through the backend's storage credentials."""
    response = _client.get_object(Bucket=NEON_STORAGE_BUCKET, Key=key)
    body = response["Body"]
    try:
        return body.read()
    finally:
        body.close()


def delete_file(key: str) -> None:
    """Best-effort cleanup; deletion failure must not break a successful replace."""
    try:
        _client.delete_object(Bucket=NEON_STORAGE_BUCKET, Key=key)
    except Exception:
        # The current CV has already been saved in the database. A stale old
        # object is preferable to reporting a failed replacement.
        pass
