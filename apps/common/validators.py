"""Shared upload validators.

`apps.common` is a plain utility package (no models, not an installed app).
These validators harden every ImageField in the project against oversized
uploads and decompression-bomb images. Attach them to a field's `validators`
list, e.g.::

    design_image = models.ImageField(
        upload_to='design_requests/',
        validators=IMAGE_VALIDATORS,
    )
"""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
MAX_IMAGE_SIZE_MB = 5
# Guards against decompression-bomb images (huge pixel dimensions in a small
# file). 6000px comfortably covers real design photos/mockups.
MAX_IMAGE_DIMENSION = 6000

validate_image_extension = FileExtensionValidator(
    allowed_extensions=ALLOWED_IMAGE_EXTENSIONS
)


def validate_image_size(value):
    if value.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            f'Image must be at most {MAX_IMAGE_SIZE_MB} MB.'
        )


def validate_image_dimensions(value):
    """Reject images whose width or height exceeds the cap.

    Reads the image with Pillow, then rewinds the file pointer so the
    subsequent save reads it from the start. Any decode error is left to
    ImageField's own validation (which runs alongside this one).
    """
    from PIL import Image

    try:
        value.seek(0)
        with Image.open(value) as img:
            width, height = img.size
    except Exception:
        return
    finally:
        try:
            value.seek(0)
        except Exception:
            pass

    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise ValidationError(
            f'Image dimensions must be at most '
            f'{MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION} pixels.'
        )


# Convenience bundle to attach to an ImageField.
IMAGE_VALIDATORS = [
    validate_image_extension,
    validate_image_size,
    validate_image_dimensions,
]
