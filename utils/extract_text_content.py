from io import BytesIO
from PyPDF2 import PdfReader


async def extract_text_content(file, mime_type):
    """Extracts text content from a file based on its MIME type."""
    if mime_type == "application/pdf":
        # Handle PDF files
        content = BytesIO(await file.download_as_bytearray())
        reader = PdfReader(content)
        return "\n".join([page.extract_text() for page in reader.pages])
    elif mime_type.startswith("image/"):
        # Handle image files
        return f"[Image content detected: {mime_type}]"
    else:
        # Handle unsupported file types
        return "[File content]"
