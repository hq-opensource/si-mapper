import mimetypes
import logging
from pathlib import Path
from urllib.parse import urlparse
import requests
from google.genai import types

# Configure a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_csv_part(file_path: str) -> types.Part:
    """
    Loads CSV content from a local file and returns a `types.Part` object.
    """
    path = Path(file_path).expanduser()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File does not exist: {path}")

    mime_type, _ = mimetypes.guess_type(str(path))
    # Fallback to text/csv if detection fails or is generic text
    if not mime_type or mime_type == "text/plain": 
         if path.suffix.lower() == ".csv":
             mime_type = "text/csv"

    if not mime_type or not mime_type.startswith("text/csv"):
         # Ideally strictly enforce, but sometimes CSVs are text/plain. 
         # Let's rely on extension primarily if mime guess is unsure.
         if path.suffix.lower() != ".csv":
            raise ValueError(f"File is not a CSV or MIME type could not be determined: {file_path}. Deteted: {mime_type}")

    with open(path, "rb") as f:
        data = f.read()
    return types.Part.from_bytes(data=data, mime_type=mime_type)

def load_pdf_part(file_path: str) -> types.Part:
    """
    Loads PDF content from a local file and returns a `types.Part` object.
    """
    path = Path(file_path).expanduser()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File does not exist: {path}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("application/pdf"):
        raise ValueError(f"File is not a PDF or MIME type could not be determined: {file_path}")

    with open(path, "rb") as f:
        data = f.read()
    return types.Part.from_bytes(data=data, mime_type=mime_type)

def load_image_part(file_path_or_url: str) -> types.Part:
    """
    Loads image content from a local file or a remote URL and returns a `types.Part` object,
    which wraps the image data along with its MIME type (e.g., image/jpeg or image/png).

    Args:
        file_path_or_url (str): The file path (local) or URL (remote) of the image.

    Returns:
        types.Part: A Gemini-compatible Part containing the image as inline binary data.
    """

    logger.debug("[ImageLoader] Loading image from: %s", file_path_or_url)

    try:
        # -------------------------------------------------------------
        # Step 1: Determine the correct MIME type from the file extension
        # -------------------------------------------------------------
        def get_mime_type(path: str) -> str:
            """
            Infers the MIME type based on file extension (jpg, jpeg, png).
            Raises an error if the format is not supported.
            """
            ext = path.lower().split(".")[-1]  # Get the last part after the dot, e.g., 'jpg'
            if ext in ["jpg", "jpeg"]:
                return "image/jpeg"
            elif ext == "png":
                return "image/png"
            else:
                # Try mimetypes
                mime, _ = mimetypes.guess_type(path)
                if mime and mime.startswith("image/"):
                    return mime
                raise ValueError(f"Unsupported image format: {ext}. Please use JPG or PNG.")

        # -------------------------------------------------------------
        # Step 2: If it's a URL (starts with http or https)
        # -------------------------------------------------------------
        if urlparse(file_path_or_url).scheme in ("http", "https"):
            logger.debug("[ImageLoader] Detected remote URL. Attempting to fetch via HTTP...")

            # Determine MIME type from URL string
            mime_type = get_mime_type(file_path_or_url)

            # Send GET request to the URL
            resp = requests.get(file_path_or_url)
            logger.debug("[ImageLoader] HTTP status: %s", resp.status_code)
            if resp.status_code == 200:
                # Read the image content into memory
                data = resp.content
                logger.debug("[ImageLoader] Remote image loaded successfully.")

                # Wrap the image bytes inside a Part with MIME type
                return types.Part.from_bytes(
                    data=data,
                    mime_type=mime_type
                )
            else:
                raise Exception(f"Failed to load image from URL: HTTP {resp.status_code}")

        # -------------------------------------------------------------
        # Step 3: If it's a local file path
        # -------------------------------------------------------------
        else:
            # Expand ~ to full home path if used
            path = Path(file_path_or_url).expanduser()
            logger.debug("[ImageLoader] Interpreted as local path: %s", path)
            logger.debug("[ImageLoader] Exists: %s, Is File: %s", path.exists(), path.is_file())

            # Check that file actually exists and is a regular file
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"File does not exist: {path}")

            # Determine MIME type from the file extension
            mime_type = get_mime_type(str(path))

            # Open and read file bytes into memory
            with open(path, "rb") as f:
                data = f.read()
                logger.debug("[ImageLoader] Local image loaded successfully, size = %s bytes", len(data))

                # Wrap the image data into a Gemini Part
                return types.Part.from_bytes(
                    data=data,
                    mime_type=mime_type
                )

    # -------------------------------------------------------------
    # Step 4: Handle errors
    # -------------------------------------------------------------
    except Exception as e:
        logger.error("[ImageLoader] ERROR: %s", e)
        # Wrap and re-raise the error with a clearer message
        raise RuntimeError(f"Image loading failed: {e}")
