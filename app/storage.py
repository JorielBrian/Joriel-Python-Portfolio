import os
import uuid

import boto3


# Keep the Neon Object Storage bucket private. Only this backend uses these
# credentials; browsers receive files through the authenticated S3 client below.
NEON_STORAGE_ENDPOINT = os.environ["NEON_STORAGE_ENDPOINT"]
NEON_STORAGE_ACCESS_KEY_ID = os.environ["NEON_STORAGE_ACCESS_KEY_ID"]
NEON_STORAGE_SECRET_ACCESS_KEY = os.environ["NEON_STORAGE_SECRET_ACCESS_KEY"]
NEON_STORAGE_BUCKET = os.environ["NEON_STORAGE_BUCKET"]

_client = boto3.client(
    "s3",
    endpoint_url=NEON_STORAGE_ENDPOINT,
    aws_access_key_id=NEON_STORAGE_ACCESS_KEY_ID,
    aws_secret_access_key=NEON_STORAGE_SECRET_ACCESS_KEY,
    region_name="auto",
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
