import os
import uuid
import boto3

# Neon Storage is S3-compatible — same boto3 client code as AWS S3 or
# Cloudflare R2 would use, just pointed at Neon's endpoint instead.
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


def upload_file(file_bytes: bytes, original_filename: str, content_type: str) -> tuple[str, str]:
    """Uploads a file to the bucket. Returns (object_key, public_url).
    A random prefix on the key avoids any caching serving a stale file
    under the same name after a replace."""
    extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "bin"
    key = f"resume/{uuid.uuid4().hex}.{extension}"

    _client.put_object(
        Bucket=NEON_STORAGE_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
        ContentDisposition=f'inline; filename="{original_filename}"',
    )
    # public_read buckets serve objects directly at this path.
    public_url = f"{NEON_STORAGE_ENDPOINT}/{NEON_STORAGE_BUCKET}/{key}"
    return key, public_url


def delete_file(key: str) -> None:
    """Best-effort delete — a failure here shouldn't block a new upload."""
    try:
        _client.delete_object(Bucket=NEON_STORAGE_BUCKET, Key=key)
    except Exception:
        pass
