from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_PIXELS = 20_000_000


class InvalidImageError(ValueError):
    pass


def process_image(data: bytes) -> tuple[bytes, int, int]:
    """Validate, orient, strip metadata, and normalize an upload to WebP."""
    if not data:
        raise InvalidImageError("The selected image is empty.")
    try:
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
        with Image.open(BytesIO(data)) as source:
            if source.format not in {"JPEG", "PNG", "WEBP", "GIF"}:
                raise InvalidImageError("Use a JPEG, PNG, WebP, or GIF image.")
            source.verify()
        with Image.open(BytesIO(data)) as source:
            image = ImageOps.exif_transpose(source)
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise InvalidImageError("The image dimensions are too large.")
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            output = BytesIO()
            image.save(output, format="WEBP", quality=86, method=6)
            return output.getvalue(), image.width, image.height
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("The uploaded file is not a valid supported image.") from exc
