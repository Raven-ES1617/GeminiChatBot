from PyPDF2 import PdfReader
from io import BytesIO
from config import settings


async def validate_file(file, mime_type):
    """Validates the file size and type."""
    if file.file_size > settings.Settings.MAX_FILE_SIZE:
        return False, f"File size exceeds {settings.Settings.MAX_FILE_SIZE // 1024 // 1024}MB limit"

    # Check file type
    allowed_types = settings.Settings.ALLOWED_FILE_TYPES
    if mime_type not in allowed_types:
        return False, f"Unsupported file type. Allowed: {', '.join(allowed_types)}"

    return True, "Valid file"


async def extract_text_content(file):
    if file.mime_type == "application/pdf":
        content = BytesIO(await file.download_as_bytearray())
        reader = PdfReader(content)
        return "\n".join([page.extract_text() for page in reader.pages])
    elif file.mime_type.startswith("image/"):
        return "[Image content detected]"
    return "[File content]"
